function getTaskInfo(taskid){

	console.log('Get task info called');
	
var taskinprogressinfo = {};
$.getJSON( '/task/' + taskid + '/status/', function(taskinprogressinfo){

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
            console.log(failedtaskinfo1);
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
    console.log('progress percent');
    console.log(progressresult);
    infohtml = infohtml + '<progress value=' + progressresult + ' max="100"></progress>';
    console.log('progresshtml');
    console.log(infohtml);
	 }
    return infohtml;

}

function successtask(result){
    infohtml = 'Request is successful<br><br>'
    + '<table>'
    + '<tr><td>Category: </td><td></td><td>' + result['category'] + '</td></tr>'
    + '<tr><td>Label: </td><td></td><td>' + result['label'] + '</td></tr>'
    + '<tr><td>User: </td><td></td><td>' + result['user'] + '</td></tr>'
    + '<tr><td>Request purpose: </td><td></td><td>' + result['reqpurpose'] + '</td></tr>'
    + '</table>';
    
    var statuslist = result['statuslist'];
    if (statuslist.length > 0){
    
    var statuslisthtml = '<br>Status<br><table>';
    
    for (i = 0; i < statuslist.length; i++){
    
    statuslisthtml = statuslisthtml + '<tr><td>' + statuslist[i] + '<td></tr>';
    
    }

    statuslisthtml = statuslisthtml + '</table>';
    infohtml = infohtml + statuslisthtml;
    }
    
    var statusdetail = result['statusdetail'];
    console.log(statusdetail);
    if (statusdetail != undefined){
    var statusdetailhtml = '<br>Status info<br><table>';
    for (i = 0; i < statusdetail.length; i++){
    statusdetailhtml = statusdetailhtml + '<tr><td>' + statusdetail[i] + '<td></tr>';
    }
    statusdetailhtml = statusdetailhtml + '</table>'
    infohtml = infohtml + statusdetailhtml;
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

var  failedTaskshtml = '<b>The request failed</b><br>';
var typeoferror = failresult['py/object'];

var typeoferror = failresult['py/object'];
var errortype = typeoferror;
var reduce = failresult['py/reduce'];
if(typeoferror =='controlarea.tasks.ControlareaException'){
	
	console.log('This is a known error');
	errortype = 'Controlarea'

var getmore = reduce[1];
	console.log('getmore');
	console.log(getmore);
var ourtuple = getmore['py/tuple'];
	console.log('our tuple');
	console.log(ourtuple)
var moreinfo = ourtuple[0];
	console.log('moreinfo');
	console.log(moreinfo);
    var taskcategory = moreinfo['category'];
    console.log('taskcategory');
    console.log(taskcategory);
    var tasklabel = moreinfo['label'];
    console.log('tasklabel');
    console.log(tasklabel);
    if(tasklabel == 'Test task'){
    	taskstatuslist = ['Test1','Test2','Test3'];
    }
    
    else{
    taskstatuslist = moreinfo['statuslist'];
    console.log('taskstatuslist');
    console.log(taskstatuslist);
    }
	var taskrequestpurpose = moreinfo['reqpurpose'];
	console.log('taskrequestpurpose');
	console.log(taskrequestpurpose);
	var taskuser = moreinfo['user'];
	console.log('taskuser');
   console.log(taskuser);
    var ipuuid = moreinfo['ipuuid'];
	var taskerrorlist = [];
	if(tasklabel == 'Test task'){
		taskerrorlist = 'Some random error';
	}
	else{
		taskerrorlist = moreinfo['errorlist'][0];
	}
		
	//failedTaskshtml =  failedTaskshtml +  'Controlareaexception';
	failedTaskshtml = failedTaskshtml + '<br>'+ 'FAILURE' + '<br>' + 'Controlarea' +  '<br><br>' + '<b>IP UUID: </b>' + ipuuid + '<br>'+ '<b> Request purpose: </b>'+ taskrequestpurpose + '<br><b> Action:</b> ' + tasklabel + '<br><b> Errorlist: </b> ' + taskerrorlist;

}

else{
//failedTaskshtml =  failedTaskshtml + '<tr><td>' + failedtasks[i].status + '</td><td>' + errortype + '</td><td>' + failedtasks[i].result + '</td></tr>';
failedTaskshtml = failedTaskshtml + '<br>' + 'FAILURE' + '<br><br>' + errortype + '<br><br>' + reduce[1]['py/tuple'];

}
console.log(failedTaskshtml);
return failedTaskshtml;
	
};