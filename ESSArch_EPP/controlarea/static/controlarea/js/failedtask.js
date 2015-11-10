function getfailedtaskhtml(failresult){

var  failedTaskshtml = '<b>The request failed</b><br>';
var typeoferror = failresult['py/object'];

var typeoferror = failresult['py/object'];
var errortype = typeoferror;
var reduce = failresult['py/reduce'];
if(typeoferror =='controlarea.tasks.ControlareaException'){
	
	console.log('This is a known error');
	errortype = 'Controlarea'

var getmore = reduce[1];

var ourtuple = getmore['py/tuple'];

var moreinfo = ourtuple[0];
	
    var taskcategory = moreinfo['category'];
    var tasklabel = moreinfo['label'];
    
    if(tasklabel == 'Test task'){
    	taskstatuslist = ['Test1','Test2','Test3'];
    }
    
    else{
    taskstatuslist = moreinfo['statuslist'];
    }
	var taskrequestpurpose = moreinfo['reqpurpose'];

	var taskuser = moreinfo['user'];

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
	
return failedTaskshtml;
	
};