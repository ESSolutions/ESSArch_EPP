function aiclist(JSONlink, createlink){
$(document).ready(function(){
$.getJSON( JSONlink, function(listinfo1) {

	 info = listinfo1;
	 populatelist();
     $('.collaptable').aCollapTable({ 
     startCollapsed: true,
     addColumn: false, 
     plusButton: '<span class="i">+</span>', 
     minusButton: '<span class="i">-</span>' 
    });
});
});

var info = {};
var tabletext = '';

function StatusProcessChoices(Process){
       
       var StatusProcessText = "";
       
       switch(Process){
            case 3000:
                StatusProcessText = 'Archived';
                break;
            case 5000:
                StatusProcessText = 'Controlarea';
                break;
            case 5100:
                StatusProcessText = 'Workarea';
                break;
            case 9999:
                StatusProcessText = 'Deleted';
                break;
            default:
                StatusProcessText ='Not known';           
       }

        return StatusProcessText;
   };

function populatelist(){
    
    if(info.length == 0){
        tabletext = 'List is empty';
    }
    
    for (i = 0; i < info.length; i++){
    tabletext = tabletext 
    + '<tr data-id="' 
    + info[i].AIC_UUID + '" data-parent="">'
    + '<td>AIC</td>'
    + '<td>' + info[i].Archivist_organization + '</td>' 
    + '<td>' + info[i].Label + '</td>' 
    + '<td>' + info[i].create_date +'</td>'
    + '<td>' + '</td>'
    + '<td>' + '</td>'
    + '<td>' + '</td>'
    + '<td>' + info[i].AIC_UUID + '<td>'
    + '</tr>';
    
   var IPList = info[i].IPs
   var parent = info[i].AIC_UUID
   
   for (j = 0; j < IPList.length; j++){
        tabletext = tabletext
        + '<tr data-id=' + IPList[j].ObjectUUID + ' '
        + 'data-parent=' + parent + '>'
        + '<td><a href="'+ createlink + IPList[j].id +'/"> IP_' + IPList[j].Generation + '</a></td>'
        + '<td> ' + IPList[j].Archivist_organization + ' </td>'
        + '<td> ' + IPList[j].Label + ' </td>'
        + '<td> ' + IPList[j].create_date + ' </td>'
        + '<td> ' + IPList[j].startdate + ' </td>'
        + '<td> ' + IPList[j].enddate + ' </td>'
        + '<td> ' + StatusProcessChoices(IPList[j].Process) + ' </td>'
        + '<td> ' + parent + ' <td>'
        + '<td> ' + IPList[j].ObjectUUID + ' <td>'
        + '</tr>'
    }
    
    
    
        
    }
 document.getElementById("AIC-table").innerHTML = tabletext;
 };
};