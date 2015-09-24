jQuery.fn.dataTableExt.oApi.fnMultiFilter = function( oSettings, oData ) {
    for ( var key in oData )
    {
        if ( oData.hasOwnProperty(key) )
        {
            for ( var i=0, iLen=oSettings.aoColumns.length ; i<iLen ; i++ )
            {
                if( i == key )
                {
                    // Add single column filter
                    oSettings.aoPreSearchCols[ i ].sSearch = oData[key][0];
                    oSettings.aoPreSearchCols[ i ].bRegex = oData[key][1];
                    break;
                }
                /*
                if( oSettings.aoColumns[i].sName == key )
                {
                    // Add single column filter
                    oSettings.aoPreSearchCols[ i ].sSearch = oData[key];
                    //oSettings.aoPreSearchCols[ i ].bRegex = oData[key][1];
                    break;
                }
                */
            }
        }
    }
    this.oApi._fnReDraw( oSettings );
};