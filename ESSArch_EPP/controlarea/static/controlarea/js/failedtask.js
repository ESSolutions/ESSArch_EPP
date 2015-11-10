function getfailedtaskhtml(taskid){
   
	console.log('The remote function is called');
	console.log('taskid');
	console.log(taskid);
	//var failinfo = {};
	
	//var taskJSON = getinfo();
	//console.log(taskJSON);
	var taskstring = 'some random html';
	//getfailiurehtml(taskJSON);
	console.log('Is the string ready?')
	console.log(taskstring);
	
	$.getJSON( '/controlarea/taskresult/' + taskid, function(failinfo)
			
		});
	
	
	return taskstring;
	
};

/*
function getinfo(){

	console.log('This function is also called');
	$.getJSON( '/controlarea/taskresult/' + taskid, function(failinfo)
		
	});//end of JSON request

	return failinfo;
	
};

function getfailiurehtml(failresult){
	console.log('The last function is called');
	console.log(failresult);
	var workedonstring = 'New html';
	/*
	var failedtaskhtml = '<b> The request failed </b>';
	console.log('This function is called');
	//console.log(failedtaskhtml);
	var typeoferror = failresult['py/object'];
	var errortype = typeoferror;
	console.log('This is the errortype');
	console.log(errortype);
	
	if(typeoferror =='controlarea.tasks.ControlareaException'){
		errortype = 'Controlarea'
		
		var reduce = failresult['py/reduce'];
		var getmore = reduce[1];
		var ourtuple = getmore['py/tuple'];
		var moreinfo = ourtuple[0];	
	    var taskcategory = moreinfo['category'];
	    var taskstatuslist = moreinfo['statuslist'];
		var tasklabel = moreinfo['label'];
		var taskrequestpurpose = moreinfo['reqpurpose'];
		var ipuuid = moreinfo['ipuuid'];
		var taskuser = moreinfo['user'];
		var taskerrorlist = moreinfo['errorlist'][0];

		failedtaskhtml = failedtaskhtml + '<b> IP UUID: </b>' + ipuuid +'<br><b> User: </b>' + taskuser + '<br><b> Request purpose: </b>'+ taskrequestpurpose + '<br><b>  Action: </b> ' + tasklabel + '<br><b> Errorlist:</b> ' + taskerrorlist + '<br>';
	}
	
	else{

	failedtaskhtml = failedtaskhtml + ' Errortype: ' + errortype + 'Cause: ' +  failresult + '<br>';
	console.log('Else is called');
	console.log(failedtaskhtml);
	}
	
	console.log('This is what we want to return');
	console.log(failedtaskhtml);
	*/
	//return workedonstring;
 //}

	/*
	console.log('This what we acctually return');
	console.log(failedtaskhtmlfinal);
	return failedtaskhtmlfinal;
*/

