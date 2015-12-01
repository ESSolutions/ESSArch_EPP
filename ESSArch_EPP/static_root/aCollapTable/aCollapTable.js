/*
 * jQuery Alvaro's Collaptable 1.0.2
 *
 * Copyright (c) 2010 Alvaro Véliz Marín - yo@alvaroveliz.cl
 *
 * Licensed under the MIT license:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * More info in http://github.com/alvaroveliz/aCollapTable
 * This is a Internet Explorer fic written by: https://github.com/cengler
 */

(function($){
  $.fn.extend({ 
    aCollapTable: function(options) {
      var defaults = {
        startCollapsed : false,
        addColumn: true,
        plusButton: '+',
        minusButton: '-'
      };
      var options = $.extend(defaults, options);
      var self = this;  
      var parents = [];

      var _collaptable = function($element, $parentVar, $display)
      {
        $parentVar = (typeof($parentVar) == 'undefined') ? $element.parents('tr').data('id') : $parentVar;
        $display = (typeof($display) == 'undefined') ? ( ($element.hasClass('act-expanded')) ? 'none' : 'table-row' ) : $display;
        table = self;

        $('tr[data-parent='+$parentVar+']', table).each(function(key, item){
          $(item).css('display', $display);
          if ($(item).hasClass('act-tr-expanded')) {
            _collaptable($element, $(item).data('id'), $display);   
          }
        });

        spacer = _getSpacer($element.parents('tr'));

        if ($display == 'none') {
          $element.html(spacer + options.plusButton).removeClass('act-expanded').addClass('act-collapsed');
          $element.parents('tr').addClass('act-tr-collapsed').removeClass('act-tr-expanded');
        }
        else {
          $element.html(spacer + options.minusButton).removeClass('act-collapsed').addClass('act-expanded');
          $element.parents('tr').addClass('act-tr-expanded').removeClass('act-tr-collapsed');
        }
      };

      var _levelsAndParents = function(obj)
      {
        $('tr', obj).each(function(k, item){
          if ($(item).data('id')) {
            $parentVar = { id : $(item).data('id'), parent : $(item).data('parent') };
            parents.push($parentVar);
          }
        });

        $('tr', obj).each(function(k, item){
          if ($(item).data('id')) {
            level = _getLevel($(item));
            $(item).attr('data-level', level);
          }
        });
      };

      var _getLevel = function($item, $level)
      {
        $level = (typeof($level) == 'undefined') ? 0 : $level;
        if ( $item.data('parent') == '' ) {
          return $level;
        }
        else {
          $parentVar = $('tr[data-id='+$item.data('parent')+']');
          return _getLevel($parentVar, $level+1);
        }
      };

      var _getSpacer = function($item)
      {
        spacer = '';
        for (i = 0; i < $item.data('level') ; i++) {
          spacer += '&nbsp;&nbsp;';
        }
        return spacer;
      };

      var _bindButtons = function()
      {
        $(document).on('click', '.act-button-expand', function(){
          if ( $('tr', self).length > 0 ) {
            expands = [];
            $('tr', self).each(function(k, item){
              if ($(item).hasClass('act-tr-collapsed') && $(item).css('display') != 'none') {
                expands.push($(item));
              }
            });
            $.each(expands, function(k, $item){
              _collaptable($('.act-more', $item));
            });
          }
        });

        $(document).on('click', '.act-button-collapse', function(){
          if ( $('tr', self).length > 0 ) {

          }
        });

        $(document).on('click', '.act-button-expand-all', function(){
          if ( $('tr', self).length > 0 ) {
            collapseds = [];
          $('tr', self).each(function(k, item){
              if ($(item).hasClass('act-tr-collapsed')) {
                _collaptable($('.act-more', $(item)));
            }
          });
          }
        });

        $(document).on('click', '.act-button-collapse-all', function(){
          if ( $('tr', self).length > 0 ) {
            collapseds = [];
            $('tr', self).each(function(k, item){
              if ($(item).hasClass('act-tr-expanded')) {
                _collaptable($('.act-more', $(item)));
              }
            });
          }
        });

      }

      return this.each(function() {
        var o = options;  
        var obj = $(this);
        _levelsAndParents(obj);
        _bindButtons();

        // adding minus
        if ( $('tr', obj).length > 0) {
          $('tr', obj).each(function(k, item){   
            spacer = _getSpacer($(item));

            $minus = $('<a />').attr('href', 'javascript:void(0)')
              .addClass('act-more act-expanded')
              .html(spacer + o.minusButton)
              .bind('click', function(){
                _collaptable($(this));
              })
              ;

            if ($('tr[data-parent='+$(item).data('id')+']').length > 0) {
              $button = (o.addColumn == true) ? $('<td />').html($minus) : $minus;  
              itemClass = (o.startCollapsed) ? 'act-tr-collapsed' : 'act-tr-expanded';
              $(item).addClass(itemClass);
            }
            else {
              $button = (o.addColumn == true) ? $('<td />').html(spacer+'&nbsp;&nbsp;') : spacer+'&nbsp;&nbsp;';
            }            

            if (o.addColumn == true) {  
              $(item).prepend($button);  
            }
            else {
              $(item).children(':first').prepend($button);
            }

            // level class
            $(item).addClass('act-tr-level-'+$(item).data('level'));
          });

          // start collapsed
          if (o.startCollapsed) {
            $('.act-more').each(function(k, item){
              $(item).click();
            });
          }
        }
      });
    }
  })
})(jQuery);

/*
For details see:
https://github.com/alvaroveliz/aCollapTable/issues/5
*/