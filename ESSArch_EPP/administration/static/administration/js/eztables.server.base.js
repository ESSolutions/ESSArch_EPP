(function($, Django, Demo){

    "use strict";


    $(function(){
        $('#browser-table').dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": Django.url('storagemedium-dt'),
            "fnRowCallback": Demo.colorRow
        });
    });

}(window.jQuery, window.Django, window.Demo));
