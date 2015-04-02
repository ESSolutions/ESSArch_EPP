(function($, Django, Demo){

    "use strict";

    var $table = $('#archiveobject-table');

    function fnFilterGlobal() {
        $table.dataTable().fnFilter(
            $("#global-filter").val(),
            null,
            $("#global-regex")[0].checked,
            false
        );
    }

    function fnFilterColumn(i) {
    	var oTable = $table.dataTable();
    	oTable.fnFilter(
            $("#filter-"+i).val(),
            i,
            $("#regex-"+i)[0].checked
            //false
        );
    	//alert('setdef in JS:'+i+' value:'+$("#filter-"+i).val())
    	oTable.fnSetColumnVis( i, $("#filterhide-"+i)[0].checked ? false : true );
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
    function getCopySelection(){
    	
    	copySelection = false
    	if (document.getElementById("copyonlyflag").checked == true)
        { copySelection = true;
        }
        return copySelection
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
            "sAjaxSource": Django.url('storagecheck-dt'),
            //"fnRowCallback": Demo.colorRow,
            "aoColumnDefs": [
                 { 'bVisible': false, 'aTargets': [ 1 ] },
                 { 'bRegex': true, 'aTargets': [ 4 ] }
            ],
            //"sDom": 'T<"clear">lfrtip',
            "sDom": 'lTrtip',
            "oTableTools": {
            	"sSwfPath": "/static/TableTools/media/swf/copy_csv_xls_pdf.swf",
            	"sRowSelect": "multi",
        		"aButtons": [
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
	                    "mColumns": [1,],
	                    "sFieldSeperator": ",",
	                    //"sAjaxUrl" : Django.url('admin_migrateview'),
	                    "sAjaxUrl" : Django.url('migration_create_parameter'),
	                    "fnClick": function( nButton, oConfig ) {
	                        var sData = this.fnGetTableData(oConfig);
	                        //var CompleteUrl = Django.url('migration_list');
	                        //var oSettings = oTable.fnSettings();
	                        //var oSetDT = this.s.dt;
	                        //var data=oSetDT.aoData;
	                        var data = $('input[name=target]:checked').val();
	                       
	                        var copyflag = getCopySelection()
	                        //var csr = document.getElementsByName('csrfmiddlewaretoken')[0].value;
	                        //oSetDT._iDisplayStart = 0;
	                        //oSetDT._iDisplayLength = 1000;
	                        //oSetDT.oApi._fnCalculateEnd( oSetDT );
	                        //oSetDT.oApi._fnDraw( oSetDT );
	                        if (confirm ('Do you really want to start migration to target: '+data+'?')){
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
			                                	"value": sData,
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
			                                	"value": copyflag
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
            $("#filter-"+i).keyup(createFilter(i)); 
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
