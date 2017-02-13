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
    		if(i==5){
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
        );
    }

    function createFilter(i) {
        return function() { fnFilterColumn(i); };
    }
    
    function fnApplyMulitiFilter(oSettings) {
        var oTable = $table.dataTable();
        var filterlist = function() {
          var filterdict = {};
          for (var i=0; i<9; i++) {
            	var regextest = false;
            	if($("#regex-" + i).length == 0){
            		if(i==5){
                		regextest = true;
            	    }
            	}
            	else{
            		regextest = $("#regex-"+i)[0].checked;
            	}
            	filterdict[i] = [$("#filter-"+i).val(), regextest];
          }
          return filterdict
        };
        oTable.fnMultiFilter( filterlist() );
    }
    
    function fnShowHide( i )
    {
    	/* Get the DataTables object again - this is not a recreation, just a get of the object */
    	var oTable = $table.dataTable();
    	var bVis = $("#filterhide-"+i)[0].checked;
    	oTable.fnSetColumnVis( i, bVis ? false : true );
    }    
    
    function createFilterHide(i) {
        return function() { fnShowHide(i); };
    }

    $(function(){
        $table.dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "aaSorting": [[5,'asc']],
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
            "sAjaxSource": "/administration/storagemigrationdt",
            "aoColumnDefs": [
                 { 'bVisible': false, 'aTargets': [ 1 ] },
                 { 'bVisible': false, 'aTargets': [ 2 ] },
                 { 'bVisible': false, 'aTargets': [ 3 ] },
                 { 'bRegex': true, 'aTargets': [ 5 ] }
            ],
            "aoSearchCols":[
                            { "sSearch": "initial", "bRegex": false}
            ],
            //"sDom": 'T<"clear">lfrtip',
            "sDom": 'lTrtip',
            "oTableTools": {
            	"sSwfPath": "/static/TableTools/media/swf/copy_csv_xls_pdf.swf",
            	"sRowSelect": "multi",
        		"aButtons": [
	             	"select_all",
	             	"select_none",
	                {
	                    "sExtends":    "ajax",
	                    "sButtonText": "Start migration",
	                    "bSelectedOnly": "true",
	                    "bHeader" : false,
	                    "sAjaxUrl" : "/administration/migreqnew",
	                    "fnClick": function( nButton, oConfig ) {
	                        var aData = this.fnGetSelectedData();                  
	                        var data = $('#filter-6').val();
							if (document.getElementById("copyonlyflag").checked == true){
								data = "Copy  Only";
								if ($('#copypath').val() == ""){
								 
									var copyPathAnswer = prompt(" You must tell us the Copy Path");
									document.getElementById("copypath").value = copyPathAnswer;
								}
								
							}
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
		                                alert( "Problem to create migration request. Please fill out all mandatory fields." );
		                            }
		                        } );
	                        }
	                        else {alert('Migration canceled');}
	                    },
	                    "fnAjaxComplete": function ( json ) {
	                    	var CompleteUrl = "/administration/migredetail/"
	                    	var req_pk = json.req_pk;
	                    	var task_id = json.task_id;
		                    alert( 'Success to create migration request' );
		                    window.location.replace(CompleteUrl + json.req_pk);
	                    }
	                },
	               
		         ]
            } 
        });
        $("#filter-submit").click(function () {fnApplyMulitiFilter()});
    });
}(window.jQuery, window.Django, window.Demo));
