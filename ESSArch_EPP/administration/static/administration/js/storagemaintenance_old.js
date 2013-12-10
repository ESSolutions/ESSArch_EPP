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
            i
            //$("#regex-"+i)[0].checked,
            //false
        );
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
            "aoColumnDefs": [
                 { 'bVisible': false, 'aTargets': [ 1 ] }
            ],
            "sDom": 'T<"clear">lfrtip',
            "oTableTools": {
            	"sSwfPath": "/static/TableTools/media/swf/copy_csv_xls_pdf.swf",
            	"sRowSelect": "multi",
        		"aButtons": [
	                {
	                    "sExtends":    "copy",
	                    "bSelectedOnly": "true"
	                },
	                {
	                    "sExtends":    "pdf",
	                    "bSelectedOnly": "true"
	                },
		         ]
            } 
        });
        //$("#global-filter").keyup( fnFilterGlobal );
        //$("#global-regex").click( fnFilterGlobal );
        for (var i=0; i<9; i++) {
            $("#filter-"+i).keyup(createFilter(i));
            //$("#regex-"+i).click(createFilter(i));
            //$("#filterhide-"+i).click(createFilterHide(i));
            $("#filterhide-"+i).click(createFilter(i));
        }
    });
}(window.jQuery, window.Django, window.Demo));
