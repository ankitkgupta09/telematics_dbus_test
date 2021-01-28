node("${node}") {
    def cancelled = false
    stage('Code pull'){
        try{
            bat '''
                cd %WORKSPACE%
                del /F /Q %WORKSPACE%\\allure-result
            '''
            env.smkoe_file = "${params.Smoke_file}"
            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId:'test_qa', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                git branch: '${branch}', credentialsId: 'test_qa', url: 'ssh://'+env.USERNAME+'@gerrit1.harman.com:29418/int_tpf/tcam2_test.git'
}
        bat '''
                cd %WORKSPACE%
                git submodule update --init --force
                git submodule foreach " git checkout feature/%COMPUTERNAME% && git pull origin feature/%COMPUTERNAME%"

            '''
        }
        catch(e){
            //  cancelled=true
             echo "EXCEPTION Caught exception: ${e}"
                }

    }
    if(cancelled){
        return
    }

  stage('Test Run') {

        script{
            println("Test Run started")

        try{
            currentBuild.displayName = "${params.test_stage}"
            env.RUN_COMMEND = ''
            if ("${params.test_stage}" != "all"){

                    if ("${params.module}" != "all"){
                        if ("${params.additional_parameters}" != "NA"){
                            env.RUN_COMMEND = "-m "+"${params.test_stage}" + " " + "test_"+"${params.module}"+".py" + " " + "${params.additional_parameters}"
                        }
                        else{
                            env.RUN_COMMEND = "-m "+"${params.test_stage}" + " " + "test_"+"${params.module}"+".py"
                        }
                    }
                    else{
                        if ("${params.additional_parameters}" != "NA"){
                            env.RUN_COMMEND = "-m "+"${params.test_stage}" + " " + "${params.additional_parameters}"

                        }
                        else{
                            env.RUN_COMMEND = "-m "+"${params.test_stage}"
                        }
                    }


                }
            else{


                    if ("${params.module}" != "all"){
                        if ("${params.additional_parameters}" != "NA"){
                            env.RUN_COMMEND = "test_"+"${params.module}"+".py" + " " + "${params.additional_parameters}"

                        }
                        else{
                            env.RUN_COMMEND = "test_"+"${params.module}"+".py"
                        }

                    }
                    // else{
                    //     println("Not provided anyting")
                    //     env.RUN_COMMEND = " "

                    // }


                }
            println("Hello after the if condition"+"${RUN_COMMEND}")

				bat'''
				        echo %RUN_COMMEND%
						sleep 2
						cd %WORKSPACE%
						call Run_Test.bat %RUN_COMMEND%
						'''
        }
		catch(e){
		    println("catch block"+e)
		    cancelled=true
		     echo ${e}
		}

		finally{
		    allure includeProperties: false, jdk: '',report: 'allure-report', results: [[path: 'allure-result']]
		       if(cancelled){
                    return
                }
		}

			}
        }

   }