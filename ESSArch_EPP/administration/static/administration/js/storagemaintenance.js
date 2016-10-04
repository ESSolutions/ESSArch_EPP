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
        );
    }

    function createFilter(i) {
        return function() { fnFilterColumn(i); };
    }

    function fnApplyMulitiFilter() {
        var oTable = $table.dataTable();
        var filterlist = function() {
          var filterdict = {};
          for (var i=0; i<9; i++) {
              filterdict[i] = [$("#filter-"+i).val(), false];
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

    function NeedToMigrateTable(json) {
        $('#need_to_migrate-table').dataTable({
        	"bPaginate": false,
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
		         ]
            }
        });
    }
    
    $(function(){
        $table.dataTable({
            "bPaginate": false,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "iDisplayLength": 10,
            "oLanguage": {
                "sLengthMenu": 'Display <select>'+
                    '<option value="-1">All</option>'+
                    '</select> records'
            },
            "sAjaxSource": "/administration/storagemaintenancedt",
            "fnServerData": function ( sSource, aoData, fnCallback ) {
                $.getJSON( sSource, aoData, function (json) {
                	//Here you can do whatever you want with the additional data
                    console.dir(json);
                    NeedToMigrateTable(json);
                    json.aaData=json.deactivate_media_list
                    json.iTotalRecords=json.deactivate_media_list.length
                    json.iTotalDisplayRecords=json.deactivate_media_list.length
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
                             { 'bRegex': true, 'aTargets': [ 4 ] }
            ],
            "aoSearchCols":[
                            { "sSearch": "initial", "bRegex": false}
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
	                    "sAjaxUrl" : "/administration/deactivatemediacreate/",
	                    "fnClick": function( nButton, oConfig ) {
	                        var aData = this.fnGetSelectedData();
	                        var aDataCol4 = [];
	                        for (var i=0;i<aData.length;i++) {
	                        	aDataCol4.push([
	                        		aData[i][4],
                        		]);
	                        }
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
		                                var oTable = $table.dataTable();
		                                oTable.fnDraw();
		                                
		                            },
		                            "dataType": "json",
		                            "type": "POST",
		                            "cache": false,
		                            "error": function () {
		                                alert( "Problem to create deactivate media request. Please fill out all mandatory fields." );
		                            }
		                        } );
	                        }
	                        else {alert('Deactivate media canceled');}
	                    },
	                },
		         ]
            } 
        });
        $("#filter-submit").click(function () {fnApplyMulitiFilter()});
    });
}(window.jQuery, window.Django, window.Demo));
