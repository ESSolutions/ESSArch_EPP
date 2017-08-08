angular.module('myApp').controller('ProfileMakerCtrl', function (ProfileMakerTemplate, $scope, $state, $rootScope, $http) {
  var vm = this;
  vm.templates = [];
  vm.template = null;
  vm.add = false;
  vm.edit = false;
  vm.generate = false;
  vm.getTemplates = function () {
    ProfileMakerTemplate.query().$promise.then(function (resource) {
      vm.templates = resource;
    });
  }
  vm.getTemplates();

  vm.editTemplate = function (tp) {
    vm.template = tp;
    vm.initEdit();
  }

  vm.showAddTemplate = function() {
    vm.add = !vm.add;
  }

  vm.showGenerateTemplate = function(tp) {
    vm.template = tp;
    vm.generate = !vm.generate;
  }

  vm.delete = function (templateName) {
    if (window.confirm('Are you sure you want to delete this template?')) {
      ProfileMakerTemplate.remove({
        templateName: templateName,
      }).$promise.then(function () {
        $state.reload();
      });
    }
  };

  vm.initEdit = function () {
    ProfileMakerTemplate.get({ templateName: vm.template.name })
      .$promise.then(function (resource) {
        $scope.treeElements = [];
        $scope.treeElements.push(vm.buildTree('root', resource.existingElements));
        vm.existingElements = resource.existingElements;
        vm.allElements = resource.allElements;
        $scope.showSelected($scope.treeElements[0]['key'], false);
        vm.edit = true;
      });
  }
  vm.countAll = {};
  vm.anyAttribute = false;
  vm.anyElement = false;
  vm.possibleChildren = [];
  vm.existingChildren = [];
  vm.existingElements = {};
  vm.choiseCount = 0;
  vm.containsFilesText = false;
  vm.choiseCount = 0

  vm.buildTree = function (uuid, data) {
    var element = data[uuid];
    var result = {}
    result['name'] = element['name'];
    result['key'] = uuid;
    var children = [];

    for (var index in element['children']) {
      var child = element['children'][index];
      children.push(vm.buildTree(child['uuid'], data));
    }
    result['children'] = children;
    return result;
  };

  // tree values
  $scope.treeOptions = {
    nodeChildren: "children",
    dirSelectable: true,
    injectClasses: {
      ul: "a1",
      li: "a2",
      liSelected: "a7",
      iExpanded: "a3",
      iCollapsed: "a4",
      iLeaf: "a5",
      label: "a6",
      labelSelected: "a8"
    }
  };
  $scope.expandedNodes = [];
  $scope.dataForTheTree = [];
  $scope.showSelected = function (sel, selected) {
    var data = vm.existingElements[sel];
    vm.selectedNode = data;
    vm.title = data['name'].charAt(0).toUpperCase() + data['name'].slice(1);
    vm.min = data['min'];
    vm.max = data['max'];
    if (vm.max == -1) {
      vm.max = 'infinite';
    }
    vm.containsFilesText = false;
    if (data['containsFiles'] == true) {
      vm.containsFilesText = true;
    }
    vm.uuid = sel;
    vm.fields = data['form'];
    if (data['userForm'].length > 0) {
      vm.fields.push({ template: '<hr/><p><b>User defined attributes</b></p>' }); //divider
      vm.fields = vm.fields.concat(data['userForm']);
    }
    var count = vm.countChildrenWithName(data['parent'], data['name']);
    if (vm.min < count) {
      vm.canDelete = true;
    } else {
      vm.canDelete = false;
    }
    // if (sel == 'root') {
    //   vm.canDelete = false;
    // }
    vm.model = data['formData'];
    vm.selectedElement = data;
    vm.anyAttribute = data['anyAttribute'];
    vm.anyElement = data['anyElement'];
    vm.possibleChildren = [];

    var groups = [];

    vm.fields.forEach(function (field) {
      var groupClass = 'display-flex';
      var fieldClass = 'flex-1';

      if (angular.equals(Object.keys(field), ['template'])) {
        var group = {
          className: groupClass,
          fieldGroup: [
            field
          ]
        }
      } else {
        var group = {
          className: groupClass,
          fieldGroup: [
            field,
            {
              className: fieldClass,
              type: 'input',
              key: field['key'] + '_desc',
              templateOptions: {
                label: 'Description'
              },
            },
            {
              className: fieldClass,
              type: 'checkbox',
              key: field['key'] + '_hideExpression',
              templateOptions: {
                label: 'Hidden'
              },
            },
            {
              className: fieldClass,
              type: 'checkbox',
              key: field['key'] + '_readonly',
              templateOptions: {
                label: 'Read Only'
              },
            },
          ]
        }
      }
      groups.push(group)
    });

    vm.fields = groups;

    //count existing children
    var existing = {};
    for (var i in data['children']) {
      var element = data['children'][i];
      if (!(element['name'] in existing)) {
        existing[element['name']] = 1
      } else {
        existing[element['name']] += 1
      }
    }
    //calculate possible children
    var allChildren = [];

    for (var i in data['availableChildren']) {
      var child = data['availableChildren'][i];
      var a = vm.calculatePossibleChildren(child, existing);
      allChildren = allChildren.concat(a);
    }

    //remove children who's already at max
    vm.possibleChildren = allChildren;
  };

  vm.calculatePossibleChildren = function (child, existing) {
    var templateElement;
    if (child['name'] in vm.allElements) {
      templateElement = vm.allElements[child['name']];
    } else {
      templateElement = 0;
    }
    var allChildren = [];
    if (child['type'] == 'element') {
      if ((!(child['name'] in existing)) || existing[child['name']] < templateElement['max'] || templateElement['max'] == -1) {
        allChildren.push(child['name']);
      }
    } else if (child['type'] == 'choise') {
      var c = vm.choiseCount.toString();
      vm.choiseCount += 1;
      allChildren.push('Choise' + c + ' Begin');
      for (var i in child['elements']) {
        var el = child['elements'][i];
        if (el['type'] == 'element') {
          if (el['name'] in existing) {
            var maxCount = templateElement['max'];
            if (maxCount == -1 || existing[el['name']] < maxCount) {
              return [el['name']];
            } else {
              return [];
            }
          } else {
            allChildren = allChildren.concat(vm.calculatePossibleChildren(el, existing));
          }
        } else {
          allChildren = allChildren.concat(vm.calculatePossibleChildren(el, existing));
        }
      }
      allChildren.push('Choise' + c + ' End');
    }
    return allChildren;
  }

  vm.countChildrenWithName = function (parentName, childName) {
    if (!parentName) {
      return 0;
    } else {
      var data = vm.existingElements[parentName];
      var count = 0;
      for (var index in data['children']) {
        var cName = data['children'][index]['name'].split('#')[0]
        var childName = childName.split('#')[0]

        if (cName == childName) {
          count += 1;
        }
      }
      return count;
    }
  };

  vm.submitForm = function () {
    var data = vm.model;
    ProfileMakerTemplate.edit({
      templateName: vm.template.name
    },
      {
        data: data,
        uuid: vm.uuid,
      }).$promise.then(function (resource) {
      });
  };

  vm.addChild = function (child) {
    ProfileMakerTemplate.addChild({
      templateName: vm.template.name
    },
      {
        name: child,
        parent: vm.uuid
      }).$promise.then(function (resource) {
        $scope.treeElements = [];
        $scope.treeElements.push(vm.buildTree('root', resource));
        vm.existingElements = resource;
        $scope.showSelected(vm.uuid, false);
      });
  };

  vm.removeChild = function (child) {
    ProfileMakerTemplate.deleteElement({
      templateName: vm.template.name
    },
      {
        uuid: vm.uuid
      }).$promise.then(function (resource) {
        $scope.treeElements = [];
        $scope.treeElements.push(vm.buildTree('root', resource));
        vm.existingElements = resource;
      });
  };

  vm.addAttribute = function () {
    vm.floatingVisable = !vm.floatingVisable;
    vm.floatingmodel = [];
    ProfileMakerTemplate.getAttributes({ templateName: vm.template.name }).$promise.then(function (resource) {
      $scope.allAttributes = resource;
    });
  };

  $scope.addAttribute = function (data, parent) {
    if (data == undefined) return;

    if (parent) {
      data.key = parent.name + ':' + data.key
      data.templateOptions.label = parent.name + ':' + data.templateOptions.label
    }
    vm.fields.push(data);
    ProfileMakerTemplate.addAttribute({
      templateName: vm.template.name
    },
      {
        uuid: vm.uuid,
        data: data
      }).$promise.then(function (resource) {
        vm.floatingVisable = false;
      });
  }

  vm.saveAttribute = function () {
    var attribute = {};
    attribute['key'] = vm.floatingmodel['attribname'];
    attribute['type'] = 'input';
    var to = {};
    to['required'] = vm.floatingmodel['attribrequired'];
    to['label'] = vm.floatingmodel['attribname'];
    to['type'] = 'text';
    attribute['templateOptions'] = to;
    attribute['defaultValue'] = vm.floatingmodel['attribvalue'];
    vm.fields.push(attribute);
    vm.floatingVisable = false;
    ProfileMakerTemplate.addAttribute({
      templateName: vm.template.name
    },
      {
        uuid: vm.uuid,
        data: attribute
      });
  };

  vm.closeFloatingForm = function () {
    vm.floatingVisable = false;
    vm.floatingmodel = [];
  };

  vm.addElement = function () {
    vm.floatingElementVisable = !vm.floatingElementVisable;
    vm.floatingElementmodel = [];
    $http.get('/template/getElements/' + templateName + '/').then(function (res) {
      $scope.allElementsAvailable = res.data;
    });
  };

  $scope.addEl = function (data) {
    data['parent'] = vm.uuid;
    $http({
      method: 'POST',
      url: '/template/struct/addExtensionChild/' + templateName + '/',
      data: data
    }).then(function (res) {
      vm.floatingElementVisable = false;
      $scope.treeElements = [];
      $scope.treeElements.push(vm.buildTree('root', res.data));
      vm.existingElements = res.data;
      $scope.showSelected(vm.uuid, false);
    });
  }

  vm.saveElement = function () {
    var element = {};
    element['parent'] = vm.uuid
    // element['templateOnly'] = false;
    // element['path'] = vm.selectedNode['path']; // + number ? //set in python ?
    element['name'] = vm.floatingElementmodel['elementname'];
    if ('kardMin' in vm.floatingElementmodel) {
      element['min'] = vm.floatingElementmodel['kardMin'];
    } else {
      element['min'] = 0;
    }
    if ('kardMax' in vm.floatingElementmodel) {
      element['max'] = vm.floatingElementmodel['kardMax'];
    } else {
      element['max'] = -1;
    }
    // element['children'] = [];
    $http({
      method: 'POST',
      url: '/template/struct/addUserChild/' + templateName + '/',
      data: element
    }).then(function (res) {
      vm.floatingElementVisable = false;
      $scope.treeElements = [];
      $scope.treeElements.push(vm.buildTree('root', res.data));
      vm.existingElements = res.data;
      $scope.showSelected(vm.uuid, false);
    });
  };

  vm.closeFloatingElementForm = function () {
    vm.floatingVisable = false;
    vm.floatingmodel = [];
  };

  vm.containsFiles = function () {
    var cf = true;
    vm.containsFilesText = true;
    if (vm.existingElements[vm.uuid]['containsFiles'] == true) {
      cf = false;
      vm.containsFilesText = false;
    }
    ProfileMakerTemplate.updateContainFiles(
      { templateName: vm.template.name },
      {
        uuid: vm.uuid,
        contains_files: cf
      }).$promise.then(function (resource) {
        vm.existingElements = resource;
      });
  };

  vm.model = {
  };

  vm.fields = [];
  vm.floatingfields = [{
    key: 'attribname',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Name',
      placeholder: 'Name',
      required: true
    }
  }, {
    key: 'attribvalue',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Value',
      placeholder: 'Value',
      required: false
    }
  }, {
    key: 'attribrequired',
    type: 'checkbox',
    templateOptions: {
      type: 'checkbox',
      label: 'Required',
      required: false
    }
  },];
  vm.floatingVisable = false;
  vm.floatingElementfields = [{
    key: 'elementname',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Name',
      placeholder: 'Name',
      required: true
    }
  }, {
    key: 'textContent',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Text content',
      placeholder: 'content',
      required: false
    }
  }, {
    key: 'kardMin',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Min required count (default: 0)',
      placeholder: 'Min',
      required: false
    }
  }, {
    key: 'kardMax',
    type: 'input',
    templateOptions: {
      type: 'text',
      label: 'Max allowed count. -1 for infinite (default: -1)',
      placeholder: 'Max',
      required: false
    }
  }];
  vm.floatingElementVisable = false;

  // Generate
  vm.generateTemplate = function () {
    var data = vm.generateModel;
    ProfileMakerTemplate.generate(
      angular.extend({ templateName: vm.template.name }, data)
    ).$promise.then(function (resource) {
      console.log(resource);
    });
  };

  vm.generateModel = {
    name: "",
    profile_type: "",
    type: "",
    status: "",
    label: "",
    representation_info: "",
    preservation_descriptive_info: "",
    supplemental: "",
    access_constraints: "",
    datamodel_reference: "",
    additional: "",
    submission_method: "",
    submission_schedule: "",
    submission_data_inventory: ""
  };
  vm.generateOptions = {
    formState: {
      awesomeIsForced: false
    }
  };

  vm.generateFields = [
    {
      key: 'name',
      type: 'input',
      templateOptions: {
        label: 'Name',
        placeholder: 'Name'
      }
    },
    {
      key: 'profile_type',
      type: 'select',
      templateOptions: {
        label: 'profile Type',
        options: [
          {
            name: "Transfer Project",
            value: "transfer_project"
          },
          {
            name: "Content Type",
            value: "content_type"
          },
          {
            name: "Data Selection",
            value: "data_selection"
          },
          {
            name: "Classification",
            value: "classification"
          },
          {
            name: "Import",
            value: "import"
          },
          {
            name: "Submit Description",
            value: "submit_description"
          },
          {
            name: "SIP",
            value: "sip"
          },
          {
            name: "AIP",
            value: "aip"
          },
          {
            name: "DIP",
            value: "dip"
          },
          {
            name: "Workflow",
            value: "workflow"
          },
          {
            name: "Preservation Description",
            value: "preservation_description"
          },
          {
            name: "Event",
            value: "event"
          },
        ]
      }
    },
    {
      key: 'type',
      type: 'input',
      templateOptions: {
        label: 'Type',
        placeholder: 'Type'
      }
    },
    {
      key: 'status',
      type: 'input',
      templateOptions: {
        label: 'Status',
        placeholder: 'Status'
      }
    },
    {
      key: 'label',
      type: 'input',
      templateOptions: {
        label: 'Label',
        placeholder: 'Label'
      }
    },
    {
      key: 'representation_info',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Representation Info',
        placeholder: 'Representation Info'
      }
    },
    {
      key: 'preservation_descriptive_info',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Preservation Description Info',
        placeholder: 'Preservation Description Info'
      }
    },
    {
      key: 'supplemental',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Supplemental',
        placeholder: 'Supplemental'
      }
    },
    {
      key: 'access_constraints',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Access Constraints',
        placeholder: 'Access Constraints'
      }
    },
    {
      key: 'datamodel_reference',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Datamodel Reference',
        placeholder: 'Datamodel Reference'
      }
    },
    {
      key: 'additional',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Additional',
        placeholder: 'Additional'
      }
    },
    {
      key: 'submission_method',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Submission Method',
        placeholder: 'Submission Method'
      }
    },
    {
      key: 'submission_schedule',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Submission Schedule',
        placeholder: 'Submission Schedule'
      }
    },
    {
      key: 'submission_data_inventory',
      type: 'input',
      hideExpression: function ($viewValue, $modelValue, scope) {
        if (scope.model.profile_type == 'SIP' || scope.model.profile_type == 'DIP' || scope.model.profile_type == 'AIP') {
          return false;
        } else {
          return true;
        }
      },
      templateOptions: {
        label: 'Submission Data Inventory',
        placeholder: 'Submission Data Inventory'
      }
    }
  ];
});