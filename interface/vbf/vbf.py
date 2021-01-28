from typing import BinaryIO, Pattern, Union
import re
import io
import pprint

import vbf_parser
from utility.Diagnostics.DiagnosticsUtility import *

VBF_ENCODING = "ascii"

class vbf:
    def string_parser(self, input_string):
        final_string_list = list()
        count = 2
        for i in input_string:
            if count == 0:
                final_string_list.append(" ")
                final_string_list.append(i)
                count = 1
            else:
                final_string_list.append(i)
                count -= 1
        final_string = "".join(final_string_list)
        return final_string

    def _read_until(self, fp: BinaryIO, pattern: Union[Pattern, str]) -> bool:
        text = ""
        while not re.search(pattern, text):
            c = fp.read(1).decode(VBF_ENCODING)
            if not c:
                return False
            text += c
        return True

    def extract_header_body(self, fp: BinaryIO) -> (str, BinaryIO):
        self._read_until(fp, r"header\s*{")
        nested_level = 1
        header = []
        is_in_quotes = False
        while nested_level != 0:
            char = fp.read(1).decode(VBF_ENCODING)
            if char == "":
                raise ValueError("Reached file end before header was closed")
            header.append(char)
            if char == '"':
                is_in_quotes = not is_in_quotes
            if not is_in_quotes:
                if char == "{":
                    nested_level += 1
                elif char == "}":
                    nested_level -= 1
        return (fp, "".join(header[:-1]))
        # return fp

    def open_file_and_return_file_pointer(self, file_name):
        """
        Opens file and returns file pointer
        """
        fp = open(file_name, "rb")
        return fp

    def get_start_address(self, fp):
        """
        Reads the start address which is 4 bytes long
        """
        start_address = fp.read(4).hex()
        print("Start Address:")
        print(start_address)

    def get_length_of_data_block(self, fp):
        """
        Reads the length which is 4 bytes long
        """
        length = fp.read(4).hex()
        print("Length")
        print(length)
        return length

    def get_checksum_of_block(self, fp):
        """
        Reads the checksum which is 2 bytes long
        """
        checksum = fp.read(2).hex()
        print("Checksum")
        print(checksum)

    def get_vbf_header(self, fp):
        """
        extracts the header portion of the vbf
        """
        fp, header_body = self.extract_header_body(fp)
        vbf = vbf_parser.parse_vbf_tokens(vbf_parser.lex_vbf_header(header_body))
        return vbf

    def get_vbf_metadata(self, fp):
        """
        Extracts the metadata associated with a particular block in vbf
        StartAddress, BlockSize and Hash from VBT
        """
        metadata = dict()
        self.get_start_address(fp)
        length = self.get_length_of_data_block(fp)
        metadata["service_id"] = fp.read(2).hex()
        metadata["number_of_blocks"] = int(fp.read(2).hex(), 16)
        for i in range(0, metadata["number_of_blocks"]):
            metadata["Block" + str(i + 1)] = {
                "StartAddress": fp.read(4).hex(),
                "BlockSize": fp.read(4).hex(),
                "Hash": fp.read(32).hex()
            }
        pprint.pprint(metadata)
        self.get_checksum_of_block(fp)
        return metadata

    def increment_block_number(self, current_block_number):
        """
        Internal logic to increment the block counter
        """
        if current_block_number == 255:
            current_block_number = 0
        else:
            current_block_number += 1
        return current_block_number

    def get_block_data(self, fp):
        """
        Parses ans sends data block in 64KB chunks over UDS
        """
        self.get_start_address(fp)
        length = self.get_length_of_data_block(fp)
        count = 0
        current_size = 0
        normal_payload_length = 65533
        int_len = int(length, 16)
        block_number = 0
        first_iter = True
        while (current_size + normal_payload_length) < int_len:
            data = fp.read(normal_payload_length).hex()
            if first_iter == True:
                block_number = 1
                first_iter = False
            transfer_data_command = ('36 ' + '{0:02x}'.format(block_number) + " " + data, \
                                     '76 ' + '{0:02x}'.format(block_number)),
            # block transfer
            single_block = transfer_data_command + ("59477:Block " + str(hex(block_number)) + " Transferred",)
            validate_diagnostics_requests(single_block)
            current_size += normal_payload_length
            block_number = self.increment_block_number(block_number)
            count += 1
        print(int_len - current_size)
        block_number = self.increment_block_number(block_number)
        data = fp.read(int_len - current_size).hex()
        transfer_data_command = ('36 ' + '{0:02x}'.format(block_number) + " " + data, \
                                 '76 ' + '{0:02x}'.format(block_number)),
        last_block = transfer_data_command + ("59477:Block " + str(hex(block_number)) + " Transferred",)
        validate_diagnostics_requests(last_block)
        print(str(hex(block_number)) + ": " + data)
        print("Count")
        print(count)
        logger.debug("Count %s", count)
        self.get_checksum_of_block(fp)

    def return_header_and_metadata(self, path):
        """
        Wrapper method to return header and metadata
        """
        fp = self.open_file_and_return_file_pointer(path)
        head_data = self.get_vbf_header(fp)
        metadata = self.get_vbf_metadata(fp)
        fp.close()
        return head_data, metadata