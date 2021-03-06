/*
ESSArch is an open source archiving and digital preservation system

ESSArch Preservation Platform (EPP)
Copyright (C) 2005-2017 ES Solutions AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Contact information:
Web - http://www.essolutions.se
Email - essarch@essolutions.se
*/

angular
  .module('essarch.services')
  .factory('listViewService', function(
    Tag,
    Profile,
    IP,
    Workarea,
    WorkareaFiles,
    Order,
    IPReception,
    Event,
    EventType,
    SA,
    $q,
    $http,
    $state,
    appConfig,
    $rootScope
  ) {
    /**
     * Map given table type with an url
     * @param {String} table - Type of table, example: "ip", "events", "workspace"
     * @param {string} [id] - Optional id for url
     */
    function tableMap(table, id) {
      var map = {
        ip: 'information-packages/',
        events: 'information-packages/' + id + '/events/',
        reception: 'ip-reception/',
        workspace: 'workareas/',
        storage_medium: 'storage-mediums/',
        storage_object: 'storage-objects/',
        robot: 'robots/',
        tapeslot: 'tape-slots/',
        tapedrive: 'tape-drives/',
        robot_queue: 'robot-queue/',
        robot_queue_for_robot: 'robots/' + id + '/queue/',
        io_queue: 'io-queue/',
      };
      return map[table];
    }

    /**
     * Check number of items and how many pages a table has.
     * Used to update tables correctly when amount of pages is reduced.
     * @param {String} table - Type of table, example: "ip", "events", "workspace"
     * @param {Integer} pageSize - Page size
     * @param {Object} filters - All filters and relevant sort string etc
     * @param {String} [id] - ID used in table url, for example IP ID
     */
    function checkPages(table, pageSize, filters, id) {
      var data = angular.extend(
        {
          page: 1,
          page_size: pageSize,
        },
        filters
      );
      var url;
      if (id) {
        url = tableMap(table, id);
      } else {
        url = tableMap(table);
      }
      return $http.head(appConfig.djangoUrl + url, {params: data}).then(function(response) {
        count = response.headers('Count');
        if (count == null) {
          count = response.length;
        }
        if (count == 0) {
          count = 1;
        }
        return {
          count: count,
          numberOfPages: Math.ceil(count / pageSize),
        };
      });
    }

    //Gets data for list view i.e information packages
    function getListViewData(
      pageNumber,
      pageSize,
      filters,
      sortString,
      searchString,
      state,
      viewType,
      columnFilters,
      archived,
      workarea
    ) {
      var data = angular.extend(
        {
          page: pageNumber,
          page_size: pageSize,
          ordering: sortString,
          state: state,
          search: searchString,
          view_type: viewType,
          archived: archived,
        },
        columnFilters
      );

      if (workarea) {
        data = angular.extend(data, {workarea: workarea});
      }

      if ($rootScope.selectedTag != null) {
        return Tag.information_packages(angular.extend({id: $rootScope.selectedTag.id}, data)).$promise.then(function(
          resource
        ) {
          var count = resource.$httpHeaders('Count');
          if (count == null) {
            count = resource.length;
          }
          return {
            count: count,
            data: resource,
          };
        });
      } else {
        return IP.query(data).$promise.then(function(resource) {
          var count = resource.$httpHeaders('Count');

          if (count == null) {
            count = resource.length;
          }
          return {
            count: count,
            data: resource,
          };
        });
      }
    }

    //Fetches IP's for given workarea (ingest or access)
    function getWorkareaData(
      workarea,
      pageNumber,
      pageSize,
      filters,
      sortString,
      searchString,
      viewType,
      columnFilters,
      user
    ) {
      return Workarea.query(
        angular.extend(
          {
            workspace_type: workarea,
            page: pageNumber,
            page_size: pageSize,
            ordering: sortString,
            search: searchString,
            view_type: viewType,
            tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
            workspace_user: user.id,
          },
          columnFilters
        )
      ).$promise.then(function(resource) {
        count = resource.$httpHeaders('Count');
        if (count == null) {
          count = resource.length;
        }
        return {
          count: count,
          data: resource,
        };
      });
    }

    //Fetches IP's for given workarea (ingest or access)
    function getDipPage(pageNumber, pageSize, filters, sortString, searchString, columnFilters) {
      return IP.query(
        angular.extend(
          {
            package_type: 4,
            page: pageNumber,
            page_size: pageSize,
            ordering: sortString,
            search: searchString,
            tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
          },
          columnFilters
        )
      ).$promise.then(function(resource) {
        count = resource.$httpHeaders('Count');
        if (count == null) {
          count = resource.length;
        }
        return {
          count: count,
          data: resource,
        };
      });
      return promise;
    }
    function getOrderPage(pageNumber, pageSize, filters, sortString, searchString) {
      return Order.query({
        page: pageNumber,
        page_size: pageSize,
        ordering: sortString,
        search: searchString,
        tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
      }).$promise.then(function(resource) {
        count = resource.$httpHeaders('Count');
        if (count == null) {
          count = resource.length;
        }
        return {
          count: count,
          data: resource,
        };
      });
    }

    function getReceptionIps(pageNumber, pageSize, filters, sortString, searchString, state, columnFilters) {
      return IPReception.query(
        angular.extend(
          {
            page: pageNumber,
            page_size: pageSize,
            ordering: sortString,
            state: state,
            search: searchString,
            tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
          },
          columnFilters
        )
      ).$promise.then(function(resource) {
        count = resource.$httpHeaders('Count');
        if (count == null) {
          count = resource.length;
        }
        return {
          count: count,
          data: resource,
        };
      });
    }

    //Add a new event
    function addEvent(ip, eventType, eventDetail, outcome) {
      return Event.save({
        eventType: eventType.eventType,
        eventOutcomeDetailNote: eventDetail,
        eventOutcome: outcome.value,
        information_package: ip.id,
      }).$promise.then(function(response) {
        return response;
      });
    }
    //Returns all events for one ip
    function getEvents(ip, pageNumber, pageSize, sortString, columnFilters, searchString) {
      return IP.events(
        angular.extend(
          {
            id: ip.id,
            page: pageNumber,
            page_size: pageSize,
            search: searchString,
            ordering: sortString,
          },
          columnFilters
        )
      ).$promise.then(function(resource) {
        count = resource.$httpHeaders('Count');
        if (count == null) {
          count = resource.length;
        }
        return {
          count: count,
          data: resource,
        };
      });
    }
    //Gets event type for dropdown selection
    function getEventlogData() {
      return EventType.query().$promise.then(function(data) {
        return data;
      });
    }
    //Returns map structure for a profile
    function getStructure(profileId) {
      return Profile.get({
        id: profileId,
      }).$promise.then(function(data) {
        return data.structure;
      });
    }
    //returns all SA-profiles and current as an object
    function getSaProfiles(ip) {
      var sas = [];
      var saProfile = {
        entity: 'PROFILE_SUBMISSION_AGREEMENT',
        profile: null,
        profiles: [],
      };
      return SA.query({
        pager: 'none',
      }).$promise.then(function(resource) {
        sas = resource;
        saProfile.profiles = [];
        var promises = [];
        sas.forEach(function(sa) {
          saProfile.profiles.push(sa);
          if (
            ip.submission_agreement == sa.url ||
            (ip.altrecordids && ip.altrecordids['SUBMISSIONAGREEMENT'] == sa.id)
          ) {
            saProfile.profile = sa;
            saProfile.locked = ip.submission_agreement_locked;
            if (saProfile.profile.profile_aip) {
              promises.push(
                Profile.get({id: saProfile.profile.profile_aip}).$promise.then(function(resource) {
                  saProfile.profile.profile_aip = resource;
                })
              );
            }
            if (saProfile.profile.profile_dip) {
              promises.push(
                Profile.get({id: saProfile.profile.profile_dip}).$promise.then(function(resource) {
                  saProfile.profile.profile_dip = resource;
                })
              );
            }
          }
        });
        return $q.all(promises).then(function() {
          return saProfile;
        });
      });
    }

    //Execute prepare ip, which creates a new IP
    function prepareIp(label) {
      ip.post({
        label: label,
      }).$promise.then(function(response) {
        return 'created';
      });
    }
    //Returns IP
    function getIp(id) {
      return IP.get({
        id: id,
      }).$promise.then(function(data) {
        return data;
      });
    }
    //Returns SA
    function getSa(id) {
      SA.get({
        id: id,
      }).$promise.then(function(data) {
        return data;
      });
    }
    //Get list of files in Ip
    function getFileList(ip) {
      return getIp(ip.id).then(function(result) {
        var array = [];
        var tempElement = {
          filename: result.object_path,
          created: result.create_date,
          size: result.object_size,
        };
        array.push(tempElement);
        return array;
      });
    }

    function prepareDip(label, objectIdentifierValue, orders) {
      return IP.prepareDip({
        label: label,
        object_identifier_value: objectIdentifierValue,
        orders: orders,
      }).$promise.then(function(response) {
        return response;
      });
    }

    function createDip(ip) {
      return IP.createDip({id: ip.id}).$promise.then(function(response) {
        return response;
      });
    }

    function prepareOrder(label) {
      return Order.save({
        label: label,
      }).$promise.then(function(response) {
        return response;
      });
    }
    function getWorkareaDir(workareaType, pathStr, pageNumber, pageSize, user) {
      var sendData;
      if (pathStr == '') {
        sendData = {
          page: pageNumber,
          page_size: pageSize,
          type: workareaType,
          user: user,
        };
      } else {
        sendData = {
          page: pageNumber,
          page_size: pageSize,
          path: pathStr,
          type: workareaType,
          user: user,
        };
      }

      return $http.get(appConfig.djangoUrl + 'workarea-files/', {params: sendData}).then(function(response) {
        var count = response.headers('Count');
        if (count == null) {
          count = response.data.length;
        }
        if (response.headers()['content-disposition']) {
          return $q.reject(response);
        } else {
          return {
            numberOfPages: Math.ceil(count / pageSize),
            data: response.data,
          };
        }
      });
    }

    function getDipDir(ip, pathStr, pageNumber, pageSize) {
      if (pathStr == '') {
        sendData = {
          id: ip.id,
          page: pageNumber,
          page_size: pageSize,
        };
      } else {
        sendData = {
          id: ip.id,
          page: pageNumber,
          page_size: pageSize,
          path: pathStr,
        };
      }
      return IP.files(sendData).$promise.then(function(data) {
        var count = data.$httpHeaders('Count');
        if (count == null) {
          count = data.length;
        }
        return {
          numberOfPages: Math.ceil(count / pageSize),
          data: data,
        };
      });
    }

    function addFileToDip(ip, path, file, destination, type) {
      var src = path + file.name;
      var dst = destination + file.name;
      return WorkareaFiles.addToDip({
        dip: ip.id,
        src: src,
        dst: dst,
        type: type,
      }).$promise.then(function(response) {
        return response;
      });
    }

    function addNewFolder(ip, path, file) {
      return IP.addFile(
        {
          id: ip.id,
        },
        {
          path: path + file.name,
          type: file.type,
        }
      ).$promise.then(function(response) {
        return response;
      });
    }

    function addNewWorkareaFolder(workareaType, path, file, user) {
      return WorkareaFiles.addDirectory({
        type: workareaType,
        path: path + file.name,
        user: user,
      }).$promise.then(function(response) {
        return response;
      });
    }

    function deleteFile(ip, path, file) {
      return IP.removeFile({
        id: ip.id,
        path: path + file.name,
      }).$promise.then(function(response) {
        return response;
      });
    }

    function deleteWorkareaFile(workareaType, path, file, user) {
      return WorkareaFiles.removeFile({
        type: workareaType,
        path: path + file.name,
        user: user,
      })
        .$promise.then(function(response) {
          return response;
        })
        .catch(function(response) {
          return response;
        });
    }

    function getDir(ip, pathStr, pageNumber, pageSize) {
      if (pathStr == '') {
        sendData = {
          id: ip.id,
          page: pageNumber,
          page_size: pageSize,
        };
      } else {
        sendData = {
          id: ip.id,
          page: pageNumber,
          page_size: pageSize,
          path: pathStr,
        };
      }
      if ($state.is('home.ingest.reception') && (ip.state == 'At reception' || ip.state == 'Prepared')) {
        sendData.id = ip.object_identifier_value;
        return IPReception.files(sendData)
          .$promise.then(function(data) {
            var count = data.$httpHeaders('Count');
            if (count == null) {
              count = data.length;
            }
            return {
              numberOfPages: Math.ceil(count / pageSize),
              data: data,
            };
          })
          .catch(function(response) {
            return response;
          });
      } else {
        return IP.files(sendData)
          .$promise.then(function(data) {
            var count = data.$httpHeaders('Count');
            if (count == null) {
              count = data.length;
            }
            return {
              numberOfPages: Math.ceil(count / pageSize),
              data: data,
            };
          })
          .catch(function(response) {
            return response;
          });
      }
    }

    function getFile(ip, path, file) {
      return IP.files({
        id: ip.id,
        path: path + file.name,
      }).then(function(response) {
        return response;
      });
    }

    function getWorkareaFile(workareaType, path, file, user) {
      return WorkareaFiles.files({
        type: workareaType,
        path: path + file.name,
        user: user,
      }).then(function(response) {
        return response;
      });
    }

    return {
      getListViewData: getListViewData,
      getReceptionIps: getReceptionIps,
      addEvent: addEvent,
      getEvents: getEvents,
      getEventlogData: getEventlogData,
      getSaProfiles: getSaProfiles,
      prepareIp: prepareIp,
      getIp: getIp,
      getSa: getSa,
      getFileList: getFileList,
      getStructure: getStructure,
      getWorkareaDir: getWorkareaDir,
      getDipDir: getDipDir,
      getWorkareaData: getWorkareaData,
      addFileToDip: addFileToDip,
      addNewFolder: addNewFolder,
      addNewWorkareaFolder: addNewWorkareaFolder,
      deleteFile: deleteFile,
      deleteWorkareaFile: deleteWorkareaFile,
      prepareDip: prepareDip,
      getDipPage: getDipPage,
      getOrderPage: getOrderPage,
      prepareOrder: prepareOrder,
      createDip: createDip,
      getDir: getDir,
      getfile: getFile,
      getWorkareaFile: getWorkareaFile,
      checkPages: checkPages,
    };
  });
