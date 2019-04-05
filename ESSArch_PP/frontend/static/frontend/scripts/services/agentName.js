angular.module('essarch.services').factory('AgentName', function($filter) {
  /**
   * Returns part and main name combined
   * @param {Object} agent
   */
  function getFullName(name) {
    return (name.part !== null && name.part !== '' ? name.part + ', ' : '') + name.main;
  }

  /**
   * Builds date section for agent name
   * @param {Object} agent
   */
  function getAgentNameDates(agent) {
    return !(agent.start_date === null && agent.end_date === null)
      ? ' (' +
          (agent.start_date !== null ? $filter('date')(agent.start_date, 'yyyy') : '') +
          ' - ' +
          (agent.end_date !== null ? $filter('date')(agent.end_date, 'yyyy') : '') +
          ')'
      : '';
  }
  return {
    /**
     * Get authorized name for agent including start/end dates
     * @param {Object} agent
     */
    getAuthorizedName: function(agent, options) {
      var name;
      agent.names.forEach(function(x) {
        if (x.type.name.toLowerCase() === 'auktoriserad') {
          name = angular.copy(x);
          name.full_name = getFullName(x);
          if (angular.isUndefined(options) || (!angular.isUndefined(options) && options.includeDates !== false)) {
            if(options && options.printDates) {
            }
            name.full_name += getAgentNameDates(agent);
          }
        }
      });
      return name;
    },

    /**
     * Parse agent names setting full_name field to a combination of part and main-names
     * @param {Object} agent
     */
    parseAgentNames: function(agent, options) {
      agent.names.forEach(function(x) {
        x.full_name = getFullName(x);
        if (x.type.name.toLowerCase() === 'auktoriserad') {
          agent.full_name = getFullName(x);
          if (angular.isUndefined(options) || (!angular.isUndefined(options) && options.includeDates !== false)) {
            agent.full_name += getAgentNameDates(agent);
          }
        }
      });
    },
  };
});
