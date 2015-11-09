function getfailedtaskhtml(taskid){
	
	var JSONlink = '/taskresult/' + taskid;
	
	$.getJSON( JSONlink, function(failresult) {
	};
	
	var failedtaskhtml = '<b>The request failed<b><br>';
	
	var typeoferror = failresult['py/object'];
	var errortype = typeoferror;
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
	
	}
	
	
	return failedtaskhtml;
};