# **User guide**

## Table of Contents

  - [Introduction ESSArch](introduction-essarch)
  - [Installation](installation)

## Introduction ESSArch
ESSArch is an open source archival solution compliant to the OAIS ISO-standard. ESSArch consist of software components that provide functionality for Pre-Ingest, Ingest, Preservation, Access, Data Management, Administration and Management. ESSArch has been developed together with the National Archives of Sweden and Norway. Every software component of ESSArch can be used individually and also be easily integrated together to provide overall functionality for producers, archivists and consumers. ESSArch consist of ETP, ETA and EPP, each individually created to provide tools for long-term digital preservation.

 * ESSArch Tools for Producer (ETP) is used to prepare IPs, to create SIPs and to submit SIPs to archival institution
 * ESSArch Tools for Archivists (ETA) is used to receive SIPs and to prepare SIPs for ingest into the preservation platform
 * ESSArch Preservation Platform (EPP) is used to ingest SIPs, perform SIP2AIP, store AIPs in different archival storage according to storage methods, provide search and access functionality for consumers


## Installation
All of the ESSArch tools can be downloaded from [github](https://github.com/ESSolutions). Installation procedure is described on the ESSArch [doc site](http://doc.essarch.org/).

## ESSArch Preservation Platform(EPP)
The tool supports the E-ARK general model but can easily be configured to support any other processes and workflows. Features provided are:
* Ingest SIP
* Perform SIP to AIP
* Preservation of AIP's on different storage mediums using different storage methods
* Fetching AIP from storage to individual workspace
* Create, edit and preserve new generations of IP's
* Create DIP from an AIP or selected content fron several AIP's
* Create orders that can be completed with a DIP
* Create Submission Agreements
* Create Profile templates, selecting metadata fields, map structure etc
* Create Profiles
* Import Submission Agreements and with Profiles
* Upload content (exports/file/folders etc.) into the selected workspace IP
* Authorizations based on users, groups and permissions
* Integration possibility with Active Directory (AD)
* Translations, e.g. different languages
* Submission Agreements (SA) are supported
* SA related profiles like SIP profiles, Submit description profiles, Transfer project profiles etc.
* Ability to create new generations of SA-profiles and the SA related profiles.
* Different parallel tasks, steps and workflows can be managed, e.g. parallel work capabilities
* Events are logged during every task and step and event types can easily be configured
* Locking, unlocking and reuse/removal of IPs in conjunction with authority models
* Filter functions are provided, default Archivist organisation and Archival institution
* Search functionality, can be adjusted easily
* Add descriptive metadata for the selected prepared IP
* Different metadata standards are supported/used, like METS and PREMIS
* An API (REST) can be used to easily interact with the tool

## The User interface
The user interface is well known if you ever have used a web application.

 * **Menu** - provides functionality to prepare IP, collect content, create SIP and submit SIP
 * **Navigation view** - filter functionality for archival institutions, archivist organization and others
 * **User administration** - change password and logout functionality
 * **Task icons** - provides refresh, settings and help functionality
 * **Translation** - supports translation of UI
 * **List view** - lists all information packages
 * **Select/Edit view** - provides select, create, update functionality

### List view
The so called list view is the table of IP's that is present in all views in EPP(Reception, Approval etc).
The IP's that are listed in this view are always relevant to the current view(for example, already created SIP's are no longer visble in the Create SIP view).

![list view][list-view]

The list view has a couple of important functions built in which will be described below.
* The main funcitonality of a view, such as Prepare IP, is accessed by clicking the IP label column. These are described in the sections for the views.
* Clicking the state column will show all steps and tasks for an IP. This view has information about task and step outcome, progress and sub steps/tasks.
Click on a step or a task to get a page with more information about the step/task. This is very useful if a step/task fails because the user can access an error traceback which will help
when trying to find out where things went wrong.

![task_tree][task_tree]

![step_report][step_report]

![task_report][task_report]

* The Events column will show a list of all events for an IP. A user can add new events.
* Delete IP. A user that is either responsible or has the permission to delete can delete it.

### User settings
User settings can be found by clicking the user symbol in the top right corner and selecting "User settings".

![user settings1][user-settings1]

* The user can choose what columns should be shown in all the list views of EPP and in which order they appear.
* The columns are saved for each user, so the user "User" can have a different set of columns from login than the user "Admin" and vice versa.
* The user can change "IP view type" between "AIC" and "IP". The AIC view type will show the AIC in the top level of the list view and IP will show "IP0", the first generation of an IP.
In both view types the top level IP can be expanded by clicking the "+" sign in the first column of each row and the children IP's will be visible.
* Settings are saved when clicking the "save" button and will always be applied on the specific user.

![user settings2][user-settings2]

### Notifications
In EPP we have notifications that shows up at the top of the page when suitable. Notifications can be live or have an update interval.
To be able to have live notifications the user needs to use a browser that supports WebSockets and have Channels activated in the backend(EPP configuration).
So whenever a notification is created the user will be notified right away and if not using WebSocket they will appear in an interval. Whenever the page is refreshed the user will always be notified if there are any notifications that has not been seen. A user can manually open the notification bar by clicking the notification(Bell) icon.


When a notification is visible, the user has 4 different options

1. The plus("+") symbol expands the notification showing the five latest notifications. Becomes a minus("-") when expanded that can be used to collapse the list. This option is only available for the first notification.
2. "Clear all" removes all notifications and they can not be seen again. This option is only available for the first notification.
3. Removes notification. This option is  available for all notifications i nthe list and the next notification will pop up as the last one.
4. The cross("X") symbol closes the notification bar without removing any notifications. This option is only available for the first notification.

[user-settings1]: ./static/frontend/img/user_settings1.png "User settings"
[user-settings2]: ./static/frontend/img/user_settings2.png "User settings"
[list-view]: ./static/frontend/img/layout.png "List view"
[task_tree]: ./static/frontend/img/task_tree.png "Task tree"
[task_report]: ./static/frontend/img/task_report.png "Task report"
[step_report]: ./static/frontend/img/step_report.png "Step report"
[notifications]: ./static/frontend/img/step_report.png "Step report"

## Ingest
The Ingest section of EPP consists of 3 different pages: *Reception*, *Approval* and *Ingest workspace*. The functionality and purpose of each is described in the following 3 sub sections.

### Reception
The purpose of reception is to receive SIP's. This is the first action we can take in EPP.

#### Receive(guide)
To receive one or many SIP's: check the checkboxes of the SIP's to receive and click the "Receive" button.
Individual popup modals for each IP will pop up in the same order as they were selected. An IP can be skipped by clicking the "Skip" button and the IP will be unchecked in the list view aswell.
The "Cancel" button will close the modal without showing the next one, keeping the SIP's selected in the list view.

If the SIP has a Submission Agreement selected from ETP it will be automatically chosen and can not be changed, but if it's not, a Submission Agreement in EPP can be chosen for the SIP. When satisfied with choice of SA click the "Prepare" button to prepare the IP. Prepared basically means that an IP has been loaded into the EPP database which requires a Submission Agreement.
When an IP has been prepared the user can edit profile values specific to this individual IP and save them. When satisfied check the "Approved to receive" checkbox and click the "Receive" button.
When receive is done the IP will be an AIP and is moved to "Approval".

### Approval
Once and IP has been received, it is placed in the Approval section. The main purpose of the approval page is to Preserve the AIP and/or Get the AIP to Ingest Workspace.
Clicking an AIP will enable a "Request form" which allows the user to choose which type "request" to be done, enter information needed for a request and sending the request.

#### Preserve
Preserves/archives and AIP. After preservation the IP will be available from the "Access" section.

#### Get
Get basically means fetching an AIP to and individual workspace and there are a couple of variations of the Get request.
1. Get. Moves a read-only version of an AIP to the Ingest Workspace.
2. Get as new generation. Creates a new generation of an AIP which from the start is identical to the previous AIP. This AIP can be edited with internal or external tools in the workspace.

### Ingest workspace
when an AIP has arrived at the workspace it can be read-only or a new generation.
A read-only AIP can not be altered in work area. It can only be inspected.
A new generation is basically a brand new IP and can be altered as much as the user wants to using internal tools or external tools.
When a user feels satisfied with the new generation of the IP it can be Preserved or moved to "Approval". This can be achieved by clicking the IP, which enables the "Request form", select request type and options and click "Submit".

## Access
The Access section of EPP consists of 3 different pages: *Search*, *Access workspace* and *Dissemination*. The functionality and purpose of each is described in the following 3 sub sections.
### Search
The purpose of the search section is to browse Archived IP's and Get the to Access workspace to edit and preserve again or Get to Access workspace to make the content available in the Dissemination section.

We can Get IP's from storage in 3 different ways:
1. Get. Gets the IP extracted as Read-only. The content of the IP is avalable in Dissemination and can be added to a DIP.
2. Get as container. Gets the IP as Read-only and not extracted. The content of the IP is avalable in Dissemination and can be added to a DIP.
3. Get as new generation. Get as new generation. Creates a new generation of an AIP which from the start is identical to the previous AIP. This AIP can be edited with internal or external tools in the workspace.

### Access workspace
when an AIP has arrived at the workspace it can be read-only or a new generation, extracted or not extracted.
A read-only AIP can not be altered in work area. It can only be inspected and added to a Dissemination(DIP).
A new generation is basically a brand new IP and can be altered as much as the user wants to using internal tools or external tools.
When a user feels satisfied with the new generation of the IP it can be Preserved or moved to "Approval". This can be achieved by clicking the IP, which enables the "Request form", select request type and options and click "Submit".

### Dissemination
the purpose of the Dissemination page is to create DIP's.
A user can prepare a new DIP and add content to it. The content that can be added to a DIP is the content of the IP's in the Access workspace.
When preparing a DIP the user can map it to a corresponding order.

## Orders
A user can create an order which can be mapped to a DIP in the Dissemination section.

## Administration
The Administration allows a user with Admin permissions to have more control and execute some of the more sensitive tasks concerning storage, profiles etc.
The Administration section of EPP consists of 6 different pages: *Media information*, *Robot information*, *Queues*, *Storage migration*, *Storage maintenance* and *Profile manager*. The functionality and purpose of each is described in the following 6 sub sections.

### Media information
TBI
### Robot information
TBI
### Queues
TBI
### Storage migration
TBI
### Storage maintenance
TBI
### Profile manager
The Profile manager section of EPP consists of 3 different pages: *SA editor*, *Profile maker* and *Import*. The functionality and purpose of each is described in the following 3 sub sections.

#### SA editor
A user can create New, edit existing and publish Submission Agreements.
A new SA can be created by using an existing SA as template.
#### Profile maker
A user can create Profile templates, selecting metadata fields, map structure etc and create Profiles

#### Import
The purpose of Import is to be able to import a Submission Agreement from another EPP instance with profiles.
Enter url of the other EPP instance with username and password and import an SA. If SA or profiles already exists, the user gets to choose between not importing or overwriting SA/profile.
