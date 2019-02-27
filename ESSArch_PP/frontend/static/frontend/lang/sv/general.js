angular.module('essarch.language').config(function($translateProvider) {
  $translateProvider.translations('sv', {
    ACCESSIP: 'Förvaringsenheter',
    ADD_ATTRIBUTE: 'Lägg till Attribut',
    ADD_EXTENSION: 'Lägg till tillägg',
    AIC_DESC: 'AIC för IP',
    APPRAISAL: 'Gallring',
    APPRAISAL_DATE: 'Gallringsfrist',
    APPRAISAL_DATE_DESC: 'Gallringsfrist',
    APPROVAL: 'Godkännande',
    ARCHIVAL_STORAGE: 'Archival storage',
    ARCHIVED: 'Arkiverad',
    ARCHIVE_POLICY: 'Arkivpolicy',
    AVAILABLE: 'Tillgänglig',
    BLOCKSIZE: 'Blockstorlek',
    CACHED: 'Cachad',
    CANCELPRESERVATION: 'Stäng arkivering',
    COLLAPSE_ALL: 'Kollapsa alla',
    CONTENTLOCATION: 'Innehållsplacering',
    COPYPATH: 'Copy path',
    COULD_NOT_LOAD_PATH: 'Kunde inte ladda sökväg!',
    CREATEDIP: 'Skapa utlämnande',
    CREATE_TEMPLATE: 'Skapa template',
    CURRENTMEDIUMID: 'nuvarande media-ID',
    CURRENTMEDIUMPREFIX: 'Nuvarande medie-prefix',
    DEACTIVATEMEDIA: 'Deactivera media',
    DEACTIVATESTORAGEMEDIUM: 'Deaktivera lagringsmedia',
    DESCRIPTION: 'Beskrivning',
    DEVICE: 'Enhet',
    DIFFCHECK: 'Diff-check',
    DIR_EXISTS_IN_DIP: 'Det existerar redan en mapp med samma namn!',
    DIR_EXISTS_IN_DIP_DESC:
      'Det existerar redan en mapp med detta namn i utlämnandet. Vill du skriva över den nuvarande mappen?',
    DISSEMINATION: 'Utlämnande',
    DISSEMINATION_PACKAGES: 'Utlämnandepaket',
    DO_YOU_WANT_TO_REMOVE_ORDER: 'Vill du ta bort beställning',
    DO_YOU_WANT_TO_REMOVE_TEMPLATE: 'Vill du ta bort template?',
    EMAILS_FAILED: 'Email misslyckades',
    EMAILS_SENT: 'Email skickades',
    ENTERORDERLABEL: 'Ange etikett för beställning',
    EXPAND_ALL: 'Expandera alla',
    FILE_EXISTS_IN_DIP: 'Det existerar redan en fil med samma namn!',
    FILE_EXISTS_IN_DIP_DESC:
      'Det existerar redan en fil med detta namn i utlämnandet. Vill du skriva över den nuvarande filen?',
    FORCECOPIES: 'Tvinga ytterligare kopior på samma mål-media',
    FORMAT: 'Format',
    FORMAT_CONVERSION: 'Formatkonvertering',
    GENERATE_TEMPLATE: 'Generera template',
    GET: 'Hämta',
    GET_AS_CONTAINER: 'Hämta som container',
    GET_AS_NEW_GENERATION: 'Hämta som ny generation',
    GLOBALSEARCHDESC_ARCHIVE_CREATORS: 'Lista alla arkivbildare som associeras med söktermen',
    GLOBALSEARCHDESC_MEDIUM: 'Lista alla lagringsmedium som associeras med söktermen',
    GLOBALSEARCHDESC_MEDIUM_CONTENT: 'Lista allt innehåll i lagringsmedium som associeras med söktermen',
    GLOBALSEARCHDESC_MIGRATION: 'Lista alla migreringar som associeras med söktermen',
    GLOBALSEARCHDESC_ORDER: 'Lista alla beställningar som associeras med söktermen',
    GLOBALSEARCHDESC_QUEUE: 'Lista alla kö-objekt som associeras med söktermen',
    GLOBALSEARCHDESC_ROBOT: 'Lista alla robotar som associeras med söktermen',
    GLOBALSEARCHDESC_RULE: 'Lista alla regler som associeras med söktermen',
    GLOBALSEARCHDESC_STRUCTURES: 'Lista alla klassificeringsstrukturer som associeras med söktermen',
    GLOBALSEARCHDESC_TAPE_DRIVE: 'Lista alla bandenheter som associeras med söktermen',
    GLOBALSEARCHDESC_TAPE_SLOT: 'Lista alla bandplatser som associeras med söktermen',
    INCLUDE_AIC_XML: 'Inkludera AIC XML',
    INCLUDE_PACKAGE_XML: 'Inkludera package XML',
    INFORMATION_CLASS: 'Informationsklass',
    INGEST: 'Mottagande',
    INVENTORY: 'Inventera',
    INVENTORYROBOTS: 'Inventera robotar',
    IOQUEUE: 'IO-kö',
    IP_GENERATION: 'IP-generation: {{generation}}',
    IP_VIEW_TYPE: 'IP-visualisering',
    LOCATION: 'Placering',
    LOCATIONSTATUS: 'Placeringsstatus',
    LONGTERM_ARCHIVAL_STORAGE: 'Long-term archival storage',
    MATCH_ERROR: 'Information_class i archive policy matchar inte information_class i ip: ',
    MAXCAPACITY: 'Maxkapacitet',
    MEDIAINFORMATION: 'Mediainformation',
    MEDIA_MIGRATION: 'Mediamigrering',
    MEDIUM: 'Medium',
    MEDIUMCONTENT: 'Mediuminnehåll',
    MEDIUMID: 'Medium ID',
    MEDIUMPREFIX: 'Media-prefix',
    MISSING_AIC_DESCRIPTION: 'AIC Description-profil saknas i leveransöverenskommelse',
    MISSING_AIP: 'AIP-profil saknas i leveransöverenskommelse',
    MISSING_AIP_DESCRIPTION: 'AIP Description-profil saknas i leveransöverenskommelse',
    MISSING_DIP: 'DIP-profil saknas i leveransöverenskommelse',
    MOUNT: 'Montera',
    MOVE_TO_APPROVAL: 'Flytta till Godkännande',
    MOVE_TO_INGEST_APPROVAL: 'Flytta till Mottagande/Godkännande',
    NEEDTOMIGRATE: 'Behöver migreras',
    NEWORDER: 'Ny beställning',
    NUMBEROFMOUNTS: 'Antal monteringar',
    OBJECTIDENTIFIERVALUE: 'Object identifier value',
    OFFLINE: 'Inaktiv',
    ONLINE: 'Aktiv',
    ORDER: 'Beställning',
    ORDERS: 'Beställningar',
    OVERVIEW: 'Översikt',
    PACKAGE_TYPE_NAME_EXCLUDE: 'Exkludera paket-typ',
    PLACE_IN_CLASSIFICATION_STRUCTURE: 'Placera i klassificeringsstruktur',
    POLICYID: 'Policy-ID',
    POLICYSTATUS: 'Policy-status',
    POSTED: 'Inlagt',
    PREPAREDIP: 'Förbered utlämnande',
    PREPAREDIPDESC: 'Förbered nytt utlämnande',
    PRESERVE: 'Arkivera',
    PREVIOUSMEDIUMPREFIX: 'Föregående medie-prefix',
    PROFILEMAKER: 'Profile maker',
    PROFILEMANAGER: 'Profilhanterare',
    PUBLIC: 'Publik',
    PUBLISH: 'Publicera',
    QUEUES: 'Köer',
    READ_ONLY: 'Endast läsbar',
    REQUEST: 'Request',
    REQUESTAPPROVED: 'Förfrågan godkänd',
    REQUESTTYPE: 'Förfrågan',
    ROBOTINFORMATION: 'Robotinformation',
    ROBOTQUEUE: 'Robotkö',
    RULES_SAVED: 'Regler sparade',
    SAEDITOR: 'SA editor',
    SA_PUBLISHED: 'Leveransöverenskommelse: {{name}} har publicerats',
    SEARCH_ADMIN: 'Sök',
    SEARCH_ADMINISTRATION: 'Administration för sökvyer',
    SEE_ALL: 'Se alla',
    SELECTIONLIST: 'Selection list',
    SELECT_ORDERS: 'Välj beställningar ..',
    SELECT_TAGS: 'Välj taggar ...',
    SETTINGS_SAVED: 'Inställningar sparade',
    STARTMIGRATION: 'Starta migrering',
    STORAGE: 'Lagring',
    STORAGEMAINTENANCE: 'Lagringsunderhåll',
    STORAGEMEDIUM: 'Lagringsmedium',
    STORAGEMIGRATION: 'Lagringsmigrering',
    STORAGETARGET: 'Destination',
    STORAGE_MEDIUMS: 'Lagringsmedier',
    STORAGE_STATUS: 'Lagringsstatus',
    STORAGE_STATUS_DESC: 'Lagringsstatus, Archival storage eller Long-term archival storage',
    STORAGE_UNIT: 'Förvaringsenhet',
    STORAGE_UNITS: 'Förvaringsenheter',
    TAGS: 'Taggar',
    TAPEDRIVES: 'Bandenheter',
    TAPELIBRARY: 'Bandbibliotek',
    TAPESLOTS: 'Bandplatser',
    TARGET: 'Mål',
    TARGETNAME: 'Målnamn',
    TARGETVALUE: 'Målvärde',
    TARGET_NAME: 'Target name',
    TEMPPATH: 'Temp path',
    TOACCESS: 'för att få tillgång.',
    UNAVAILABLE: 'Inte tillgänglig',
    UNMOUNT: 'Avmontera',
    UNMOUNT_FORCE: 'Avmontera(tvinga)',
    UNSPECIFIED: 'Ospecificerad',
    USEDCAPACITY: 'Använd kapacitet',
    USE_SELECTED_SA_AS_TEMPLATE: 'Använd vald leveransöverenskommelse som mall',
    USE_TEMPLATE: 'Använd mall',
    WORKING_ON_NEW_GENERATION: '{{username}} arbetar med en ny generation av detta IP',
  });
});
