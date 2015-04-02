(function($, Django, Demo){

    "use strict";

    var $table = $('#archiveobject-table');

    function fnFilterGlobal() {
        $table.dataTable().fnFilter(
            $("#global-filter").val(),
            null,
            i,
            $("#regex-"+i)[0].checked,
            false
         );
    }

    function fnFilterColumn(i) {
    	
    	var regextest = false;
    	if($("#regex-" + i).length == 0){
    		if(i==4){
        		regextest = true;
    	    }
    	}
    	else{
    		regextest = $("#regex-"+i)[0].checked;
    	}
    	
    	var oTable = $table.dataTable();
    	oTable.fnFilter(
            $("#filter-"+i).val(),
            i,
            regextest
            //$("#filter-"+i)
            //$("#regex-"+i)[0].checked
           //$('#col'+i+'_regex').prop('checked'),
            
        );
    	//alert('setdef in JS:'+i+' value:'+$("#filter-"+i).val())
    	// oTable.fnSetColumnVis( i, $("#filterhide-"+i)[0].checked ? false : true );
    }

    function createFilter(i) {
        return function() { fnFilterColumn(i); };
    }
    
    function fnShowHide( i )
    {
    	/* Get the DataTables object again - this is not a recreation, just a get of the object */
    	var oTable = $table.dataTable();
    	
    	//var bVis = oTable.fnSettings().aoColumns[iCol].bVisible;
    	var bVis = $("#filterhide-"+i)[0].checked;
    	oTable.fnSetColumnVis( i, bVis ? false : true );
    }    
    
    function createFilterHide(i) {
        return function() { fnShowHide(i); };
    }
   
    function DeactivateMediaTable(json) {
        $('#deactivate_media-table').dataTable({
        	"sPaginationType": "bootstrap",
        	"bDestroy": true,
        	"aaData": json.deactivate_media_list,
        	"sDom": 'lTrtip',
            "oTableTools": {
            	"sRowSelect": "multi",
        		"aButtons": [
             		"select_all",
             		"select_none",
	                {
	                    "sExtends":    "ajax",
	                    "sButtonText": "Deactivate media",
	                    "bSelectedOnly": "true",
	                    "bHeader" : false,
	                    "mColumns": [0,],
	                    "sFieldSeperator": " ",
	                    "sAjaxUrl" : Django.url('deactivatemedia_create'),
	                    "fnClick": function( nButton, oConfig ) {
	                        var aData = this.fnGetSelectedData();
	                        //var sData = this.fnGetTableData(oConfig);
	                        if (confirm ('Do you really want to start deactivate media: '+aData+'?')){
		                        $.ajax( {
		                            "url": oConfig.sAjaxUrl,
		                            "data": [		                                    
											{
												"name": "ReqPurpose", 
												"value": $('#ReqPurpose').val()
											},
			                                { 
			                                	"name": "MediumList", 
			                                	"value": JSON.stringify(aData),
			                                },
			                                { 
			                                	"name": "csrfmiddlewaretoken",
			                                	"value": document.getElementsByName('csrfmiddlewaretoken')[0].value
			                                }
		                            ],
		                            "success": function () {
		                                alert( "Success to deactivate media" );
		                            },
		                            "dataType": "json",
		                            "type": "POST",
		                            "cache": false,
		                            "error": function () {
		                                alert( "Failed to deactivate media" );
		                            }
		                        } );
	                        }
	                        else {alert('Deactivate media canceled');}
	                    },
	                },
		         ]
            }
        });
    }

    function NeedToMigrateTable(json) {
        $('#need_to_migrate-table').dataTable({
        	"sPaginationType": "bootstrap",
        	"bDestroy": true,
        	"oLanguage": {
                "sLengthMenu": 'Display <select>'+
                    '<option value="10">10</option>'+
                    '<option value="25">25</option>'+
                    '<option value="50">50</option>'+
                    '<option value="100">100</option>'+
                    '<option value="250">250</option>'+
                    '<option value="500">500</option>'+
                    '<option value="1000">1000</option>'+
                    '<option value="-1">All</option>'+
                    '</select> records'
            },
        	"aaData": json.need_to_migrate_list,
        	"sDom": 'lTrtip',
            "oTableTools": {
            	"sSwfPath": "/static/TableTools/media/swf/copy_csv_xls_pdf.swf",
            	"sRowSelect": "multi",
        		"aButtons": [
//	             	"select_all",
//	             	"select_none",
//	                {
//	                    "sExtends":    "copy",
//	                    "bSelectedOnly": "true"
//	                },
//	                {
//	                    "sExtends":    "pdf",
//	                    "bSelectedOnly": "true"
//	                },
		         ]
            }
        });
    }
    
    $(function(){
        $table.dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "iDisplayLength": 10,
            "oLanguage": {
                "sLengthMenu": 'Display <select>'+
                    '<option value="10">10</option>'+
                    '<option value="25">25</option>'+
                    '<option value="50">50</option>'+
                    '<option value="100">100</option>'+
                    '<option value="250">250</option>'+
                    '<option value="500">500</option>'+
                    '<option value="1000">1000</option>'+
                    '<option value="-1">All</option>'+
                    '</select> records'
            },
            "sAjaxSource": Django.url('storagemaintenance-dt'),
            //"fnRowCallback": Demo.colorRow,
            "fnServerData": function ( sSource, aoData, fnCallback ) {
                $.getJSON( sSource, aoData, function (json) {
                	//Here you can do whatever you want with the additional data
                    console.dir(json);
                    //$('#deactivate_media').html(json.deactivate+*_media_list);
                    DeactivateMediaTable(json);
                    NeedToMigrateTable(json);
                    //Call the standard callback to redraw the table
                    fnCallback(json);
                } );
            },
            "aoColumnDefs": [
                 { 'bVisible': false, 'aTargets': [ 1 ] },
                
                 { 'bRegex': true, 'aTargets': [ 4 ] }
            ],
            //"sDom": 'T<"clear">lfrtip',
            "sDom": 'lTrtip',
            "oTableTools": {
            	"sSwfPath": "/static/TableTools/media/swf/copy_csv_xls_pdf.swf",
            	"sRowSelect": "multi",
            	//"sRowSelect": "single",
        		"aButtons": [
	             	"select_all",
	             	"select_none",
//	                {
//	                    "sExtends":    "copy",
//	                    "bSelectedOnly": "true"
//	                },
//	                {
//	                    "sExtends":    "pdf",
//	                    "bSelectedOnly": "true"
//	                },
//	                {
//	                    "sExtends":    "text",
//	                    "sButtonText": "testknapp",
//	                    "fnClick": function ( nButton, oConfig, oFlash, oTable) {
//	                    	var data = $('#filter-5').val();
//	                    	//var CSRF_TOKEN = '{{ csrf_token }}';
//	                    	var CSRF_TOKEN = document.getElementsByName('csrfmiddlewaretoken')[0].value
//	                    	//var CSRF_TOKEN = $cookies['csrftoken']
//	                        alert( 'Mouse click'+data+CSRF_TOKEN);
//	                    }
//	                },
	                {
	                    "sExtends":    "ajax",
	                    "sButtonText": "Start migration",
	                    "bSelectedOnly": "true",
	                    "bHeader" : false,
	                    //"mColumns": [1,],
	                    //"sFieldSeperator": ",",
	                    "sAjaxUrl" : Django.url('migration_create_parameter'),
	                    "fnClick": function( nButton, oConfig ) {
	                        //var sData = this.fnGetTableData(oConfig);
	                        var aData = this.fnGetSelectedData();
	                        //console.log( JSON.stringify(aData) );
	                        //var aaData = [];
	                        //for (var i=0;i<aData.length;i++) {
	                        //    //aaData.push(['row']);
	                        //	aaData.push([
	                        //		aData[i]+'\r\n',
	                        //		//'\n',
                        	//	]);
	                        //}
	                        //alert('aaData:'+aaData+'end')
	                        //console.dir(aData);	                    
	                        var data = $('#filter-5').val();

	                        if (confirm ('Do you really want to start migration to target: '+data +'?')){
		                        $.ajax( {
		                            "url": oConfig.sAjaxUrl,
		                            "data": [		                                    
			                                { 
			                                	"name": "Status", 
			                                	"value": '0',
			                                },
			                                {
			                                	"name": "TargetMediumID", 
			                                	"value": data
			                                },
			                                {
			                                	"name": "ReqPurpose", 
			                                	"value": $('#ReqPurpose').val()
			                                },
			                                { 
			                                	"name": "ObjectIdentifierValue", 
			                                	"value": JSON.stringify(aData),
			                                },
			                                {
			                                	"name": "user", 
			                                	"value": 'x'
			                                },
			                                {
			                                	"name": "ReqType", 
			                                	"value": '1'
			                                },
			                                {
			                                	"name": "Path", 
			                                	"value": $('#tmpmigpath').val()
			                                },
			                                {
			                                	"name": "CopyPath", 
			                                	"value": $('#copypath').val()
			                                },
			                                {
			                                	"name": "CopyOnlyFlag", 
			                                	"value": $('#copyonlyflag').prop('checked')? 1 : ''
			                                },
			                                {
			                                	"name": "ReqUUID", 
			                                	"value": 'x'
			                                },
			                                { 
			                                	"name": "csrfmiddlewaretoken",
			                                	"value": document.getElementsByName('csrfmiddlewaretoken')[0].value
			                                }
		                            ],
		                            "success": oConfig.fnAjaxComplete,
		                            "dataType": "json",
		                            "type": "POST",
		                            "cache": false,
		                            "error": function () {
		                                alert( "Failed to create migration request" );
		                            }
		                        } );
	                        }
	                        else {alert('Migration canceled');}
	                    },
	                    "fnAjaxComplete": function ( json ) {
	                    	//var CompleteUrl = Django.url('migration_detail');
	                    	var CompleteUrl = "/administration/migredetail/"
	                    	var req_pk = json.req_pk;
	                    	var task_id = json.task_id;
		                    alert( 'Success to create migration request' );
		                    window.location.replace(CompleteUrl + json.req_pk);
		                    //window.location.href = CompleteUrl + json.req_pk;
	                    }
	                },
	               
		         ]
            } 
        });
        //$("#global-filter").keyup( fnFilterGlobal );
        //$("#global-regex").click( fnFilterGlobal );
        for (var i=0; i<9; i++) {
        	
            if(i == 7){
            	$("#filter-"+i).change(createFilter(i));
            }
            else if(i == 5){
            	$("#filter-"+i).change(createFilter(i));
            }
            else{
            	$("#filter-"+i).keyup(createFilter(i));
            }
           
            // Set initial default values
            if ($("#filter-"+i).val()) {
            	fnFilterColumn(i)
            }
            //$("#regex-"+i).click(createFilter(i));
            //$("#filterhide-"+i).click(createFilterHide(i));
            $("#filterhide-"+i).click(createFilter(i));
        }
    });
}(window.jQuery, window.Django, window.Demo));
