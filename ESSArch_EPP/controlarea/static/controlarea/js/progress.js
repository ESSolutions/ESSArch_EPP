function getTaskInfo(taskid){

	var taskinprogressinfo = {};
	/*
	$.getJSON( '/task/' + taskid + '/status/', function(taskinprogressinfo){
	
		populateTaskInProgress(taskinprogressinfo);
		
		});
	*/
	
	$.ajaxSetup({ cache: false });
	
	$.getJSON( '/controlarea/taskresult/' + taskid + '/', function(taskinprogressinfo){	
		populateTaskInProgress(taskinprogressinfo);	
	});
	
	function populateTaskInProgress(taskinprogressinfo){
	
		var thetask = taskinprogressinfo['task'];		
		var taskhtml = determineStatus(thetask);
		
		function determineStatus(thetask){
	        var infohtml = 'No info';
	        var taskstatus = thetask['status'];
	        var taskresult = thetask['result'];
	        
	        switch(taskstatus){
	            case 'FAILURE':
	                failedtask(taskid);
	                break;
	            case 'notaskfound':
	                return infohtml;
	                break;            
	            case 'PENDING':
	                pendingtask(taskresult);
	                break;
	            case 'PROGRESS':
	                progresstask(taskresult);
	                break;
	            case 'SUCCESS':
	                successtask(taskresult);
	                break;
	            default:
	                console.log('Status undetermined');
	        }
	
			function failedtask(taskid){
			    $.getJSON( '/controlarea/taskresult/' + taskid + '/', function(failedtaskinfo1){
			            console.log('Failed task info');
			            var readable = getfailedtaskhtml(failedtaskinfo1);
			        	infohtml = readable;;
			        	 document.getElementById("taskinprogress").innerHTML = infohtml;
			        	 });
			        	//return infohtml;    
			}
			
			function pendingtask(result){
			    infohtml = '<b>The request is pending<b><br>';
			    return infohtml;
			}
			
			function progresstask(result){
				infohtml = 'Request is in progress<br><br>';
			    var progressresult = result['progress_percent'];
				if(progressresult != undefined){
					infohtml = infohtml + '<progress value=' + progressresult + ' max="100"></progress>';
				}
			    return infohtml;
			}
			
			function successtask(result){
			    infohtml = 'Result:'
			    + '<table>'
			    + '<tr><td>Category: </td><td></td><td>' + result['category'] + '</td></tr>'
			    + '<tr><td>Label: </td><td></td><td>' + result['label'] + '</td></tr>'
			    + '<tr><td>User: </td><td></td><td>' + result['user'] + '</td></tr>'
			    + '<tr><td>Request purpose: </td><td></td><td>' + result['reqpurpose'] + '</td></tr>';
			
			    var statuscode = result['statuscode'];
			    if (statuscode != undefined){
			    	if (statuscode == true){
			    		infohtml = infohtml + '<tr><td>Status: </td><td></td><td>Fail (' + statuscode + ')</td></tr>';
			    	}
			    	else if (statuscode == false){
			    		infohtml = infohtml + '<tr><td>Status: </td><td></td><td>OK (' + statuscode + ')</td></tr>';
			    	}
			    }
			    else{
			    	infohtml = infohtml + '<tr><td>Status: </td><td></td><td>OK</td></tr>';
			    }
			
			    infohtml = infohtml +  '</table>';
			    
			    var statuslist = result['statuslist'];
			    if (statuslist.length > 0){    
				    var statuslisthtml = '<br>Summary:<br><table>';
				    for (i = 0; i < statuslist.length; i++){
				        var statusitem = statuslist[i];
				        var statusiteminfo = "";
				        if(statusitem['py/tuple']){
				        	statusiteminfo = statusitem['py/tuple'][0];
				        }
				        else{
				        	statusiteminfo = statusitem;
				       }
				       statuslisthtml = statuslisthtml + '<tr><td>' + statusiteminfo + '<td></tr>';
			        }
				    statuslisthtml = statuslisthtml + '</table>';
				    infohtml = infohtml + statuslisthtml;
			    }
			    
			    var statusdetail = result['statusdetail'];
			    if (statusdetail != undefined){
			    	if (statusdetail.length==2){
			
			    		detailinfolist = statusdetail[0];
			    		if (detailinfolist.length > 0){
				    	    var statusdetailhtml = '<br>Detailed:<br><table>';
				    	    for (i = 0; i < detailinfolist.length; i++){
				    	    	statusdetailhtml = statusdetailhtml + '<tr><td>' + detailinfolist[i] + '<td></tr>';
				    	    }
				    	    statusdetailhtml = statusdetailhtml + '</table>'
				    	    infohtml = infohtml + statusdetailhtml;
			    	    }
			    		
			    	    probleminfolist = statusdetail[1];
			    	    if (probleminfolist.length > 0){
				    	    var problemdetailhtml = '<br>Problem:<br><table>';
				    	    for (i = 0; i < probleminfolist.length; i++){
				    	    	problemdetailhtml = problemdetailhtml + '<tr><td>' + probleminfolist[i] + '<td></tr>';
				    	    }
				    	    problemdetailhtml = problemdetailhtml + '</table>'
				    	    infohtml = infohtml + problemdetailhtml;
			    	    }
			    	}
			    	else{
			    	    var statusdetailhtml = '<br>Details:<br><table>';
			    	    for (i = 0; i < statusdetail.length; i++){
			    	    statusdetailhtml = statusdetailhtml + '<tr><td>' + statusdetail[i] + '<td></tr>';
			    	    }
			    	    statusdetailhtml = statusdetailhtml + '</table>'
			    	    infohtml = infohtml + statusdetailhtml;
				    }
			    }
			    
			    var resultlist = result['resultlist'];
			    if(resultlist != undefined){
				    if (resultlist.length > 0 ){
					    var resultlisthtml = '<br>Result:<br><table>';
					    for (i = 0; i < resultlist.length; i++){
					    	resultlisthtml = resultlisthtml + '<tr><td>' + resultlist[i] + '<td></tr>';
					    }
					    resultlisthtml = resultlisthtml + '</table>'
					    infohtml = infohtml + resultlisthtml;
				    }
			    }
			    return infohtml;
			}	
			return infohtml;
		};
		document.getElementById("taskinprogress").innerHTML = taskhtml;
	};
};

function getfailedtaskhtml(failinfo){
	var failedtask = failinfo['task'];
	var failresult = failedtask['result'];
	var typeoferror = failresult['py/object'];
	var errortype = typeoferror;
	var reduce = failresult['py/reduce'];
	if(typeoferror == 'controlarea.tasks.ControlareaException'){
		console.log('This is a known error');
		errortype = 'Controlarea'
		var getmore = reduce[1];
		var ourtuple = getmore['py/tuple'];
		var moreinfo = ourtuple[0];
	
	    if(moreinfo['label'] == 'Test task'){
	    	taskstatuslist = ['Test1','Test2','Test3'];
	    }
	    else{
	    	taskstatuslist = moreinfo['statuslist'];
	    }
		var taskerrorlist = [];
		if(moreinfo['label'] == 'Test task'){
			taskerrorlist = 'Some random error';
		}
		else{
			//console.log('moreinfo:'+moreinfo)
			//taskerrorlist = moreinfo['errorlist'][0];
			if (moreinfo['errorlist'] != undefined){
				taskerrorlist = moreinfo['errorlist'];
			}
			else{
				taskerrorlist = moreinfo['statusdetail'][1];
			}
		}
		
	    infohtml = '<b>The request failed</b><br>'
	    	+ '<br>Result:'
		    + '<table>'
		    + '<tr><td>Category: </td><td></td><td>' + moreinfo['category'] + '</td></tr>'
		    + '<tr><td>Label: </td><td></td><td>' + moreinfo['label'] + '</td></tr>'
		    + '<tr><td>User: </td><td></td><td>' + moreinfo['user'] + '</td></tr>'
		    + '<tr><td>Request purpose: </td><td></td><td>' + moreinfo['reqpurpose'] + '</td></tr>';
	    	+ '<tr><td>IP UUID: </td><td></td><td>' + moreinfo['ipuuid'] + '</td></tr>';
		
		    var statuscode = moreinfo['statuscode'];
		    if (statuscode != undefined){
		    	if (statuscode == true){
		    		infohtml = infohtml + '<tr><td>Status: </td><td></td><td>Fail (' + statuscode + ')</td></tr>';
		    	}
		    	else if (statuscode == false){
		    		infohtml = infohtml + '<tr><td>Status: </td><td></td><td>OK (' + statuscode + ')</td></tr>';
		    	}
		    }
		    else{
		    	infohtml = infohtml + '<tr><td>Status: </td><td></td><td>Fail</td></tr>';
		    }
		
		    infohtml = infohtml +  '</table>';		

    	    if (taskerrorlist.length > 0){
	    	    var problemdetailhtml = '<br>Problem:<br><table>';
	    	    for (i = 0; i < taskerrorlist.length; i++){
	    	    	problemdetailhtml = problemdetailhtml + '<tr><td>' + taskerrorlist[i] + '<td></tr>';
	    	    }
	    	    problemdetailhtml = problemdetailhtml + '</table>'
	    	    infohtml = infohtml + problemdetailhtml;
    	    }
	}	
	else{
	    infohtml = '<b>The request failed</b><br>'
	    	+ 'Result:'
		    + '<table>'
		    + '<tr><td>Exception: </td><td></td><td>' + errortype + '</td></tr>'
		    + '<tr><td>Error: </td><td></td><td>' + JSON.stringify(reduce[1], null, 4) + '</td></tr>'
	    infohtml = infohtml +  '</table>';
	}
	return infohtml;
};