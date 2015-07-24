(function($, Django, Demo){

    "use strict";

    var $table = $('#deactivate_media-table');

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
            i
            //$("#regex-"+i)[0].checked
            //false
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
		                                //fnReloadAjax();
		                                //fnDraw();
		                                //$('#deactivate_media-table').dataTable.ajax.reload();
		                                //DeactivateMediaTable.dataTable.ajax.reload();
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
                    //DeactivateMediaTable(json);
                    NeedToMigrateTable(json);
                    //Call the standard callback to redraw the table
                    json.aaData=json.deactivate_media_list
                    //fnCallback(json.deactivate_media_list);
                    fnCallback(json);
                } );
            },
            "aoColumnDefs": [
                             { 'bVisible': false, 'aTargets': [ 0 ] },
                             { 'bVisible': false, 'aTargets': [ 1 ] },
                             { 'bVisible': false, 'aTargets': [ 2 ] },
                             { 'bVisible': false, 'aTargets': [ 3 ] },
                             { 'bVisible': false, 'aTargets': [ 5 ] },
                             { 'bVisible': false, 'aTargets': [ 6 ] },                             
                             { 'bVisible': false, 'aTargets': [ 7 ] },
                             { 'bVisible': false, 'aTargets': [ 8 ] },
                             { 'bVisible': false, 'aTargets': [ 9 ] },
                             { 'bVisible': false, 'aTargets': [ 10 ] },
                             { 'bVisible': false, 'aTargets': [ 11 ] },
                             { 'bVisible': false, 'aTargets': [ 12 ] },
                             { 'bVisible': false, 'aTargets': [ 13 ] },
                             { 'bVisible': false, 'aTargets': [ 14 ] },
                             { 'bVisible': false, 'aTargets': [ 15 ] },
                             { 'bVisible': false, 'aTargets': [ 16 ] },                         
                             { 'bRegex': true, 'aTargets': [ 4 ] }
                        ],            
            //"sDom": 'T<"clear">lfrtip',
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
	                    "sAjaxUrl" : Django.url('deactivatemedia_create'),
	                    "fnClick": function( nButton, oConfig ) {
	                        var aData = this.fnGetSelectedData();
	                        var aDataCol4 = [];
	                        for (var i=0;i<aData.length;i++) {
	                        	aDataCol4.push([
	                        		aData[i][4],
                        		]);
	                        }
	                        //alert('aDataCol4:'+aDataCol4+'end')
	                        if (confirm ('Do you really want to start deactivate media: '+aDataCol4+'?')){
		                        $.ajax( {
		                            "url": oConfig.sAjaxUrl,
		                            "data": [		                                    
											{
												"name": "ReqPurpose", 
												"value": $('#ReqPurpose').val()
											},
			                                { 
			                                	"name": "MediumList", 
			                                	"value": JSON.stringify(aDataCol4),
			                                },
			                                { 
			                                	"name": "csrfmiddlewaretoken",
			                                	"value": document.getElementsByName('csrfmiddlewaretoken')[0].value
			                                }
		                            ],
		                            "success": function () {
		                                alert( "Success to deactivate media" );
		                                //oConfig.ajax.reload();
		                                //$('#filter-4').trigger('change');
		                                var oTable = $table.dataTable();
		                                oTable.fnDraw();
		                                
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
        //$("#global-filter").keyup( fnFilterGlobal );
        //$("#global-regex").click( fnFilterGlobal );
        for (var i=0; i<9; i++) {
        	
            if(i == 7){
            	$("#filter-"+i).change(createFilter(i));
            }
            else if(i == 4){
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
