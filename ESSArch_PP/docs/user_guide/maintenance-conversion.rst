.. _maintenance-conversion:
*******
Formatkonvertering
*******

Under konverteringssidan skapar vi konverteringsregler som körs automatiskt eller
manuellt på utvalt arkiverat material.

Skapa regel
=======

För att skapa en ny regel klickar vi på *Skapa* ovanför listan med regler.

Vi får här skriva i vad regeln ska heta, hur ofta den ska köras och vilka filer
som ska konverteras i alla kopplade AIP:er.

**Frekvens** är vad som bestämmer hur ofta en regel ska exekveras och
specificeras med en **cron**-syntax. T.ex. ``0 15 * * 3`` för varje onsdag
klockan 15.

För att lägga till en **specifikation** så skriver vi t.ex. namnet
****/*.docx** i textfältet **sökväg**, **pdf** i mål och klickar på **+**. Med
den regeln så kommer alla filer av typen **docx** att konverteras till **pdf**.

Koppla regel
=======

Om vi går till **Åtkomst/Sök**, markerar en eller flera AIP:er, högerklickar
och väljer **Konvertering** så får vi upp en lista med AIP:erna vi valt som vi då
kan expandera för att se kopplade regler.  Vi får även upp en knapp för att
lägga till nya regler.

Jobblistor
=======

Under listan med regler så har vi tre listor med konverteringsjobb som är
filtrerade utefter status på jobben. **Pågående** visar konverteringsjobb som körs
just nu, **Nästa** är jobb som kommer att exekveras och **Avslutade** är jobb
som är klara.

När en regel är kopplad till minst en AIP så kommer det skapas ett jobb under
**Nästa**. Det jobbet kan vi antingen vänta på ska exekveras automatiskt vid
tiden som står under **Start**. Alternativt kan vi klicka på
**Förhandsgranska** och sedan **Kör** för att exekvera på en gång. Jobbet
kommer då flyttas till **Pågående** och sist **Avslutade**. 

När jobbet är klart och är under **Avslutade** så kan vi klicka på **Rapport**
för att se rapporten för det jobbet.
