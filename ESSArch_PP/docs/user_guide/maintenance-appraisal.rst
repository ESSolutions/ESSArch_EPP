.. _maintenance-appraisal:
*******
Gallring
*******

Under gallringssidan skapar vi gallringsregler som körs automatiskt eller
manuellt på utvalt arkiverat material.

Skapa regel
=======

För att skapa en ny regel klickar vi på *Skapa* ovanför listan med regler.

Vi får här skriva i vad regeln ska heta, hur ofta den ska köras och vilka filer
som ska gallras i alla kopplade AIP:er.

**Frekvens** är vad som bestämmer hur ofta en regel ska exekveras och
specificeras med en **cron**-syntax. T.ex. ``0 15 * * 3`` för varje onsdag
klockan 15. För att lägga till en **sökväg** så skriver vi t.ex. namnet på en
mapp i textfältet och klickar på **+**. Vill vi gallra hela AIP:n så lämnar vi
fältet tomt.

Koppla regel
=======

Om vi går till **Åtkomst/Sök**, markerar en eller flera AIP:er, högerklickar
och väljer **Gallring** så får vi upp en lista med AIP:erna vi valt som vi då
kan expandera för att se kopplade regler.  Vi får även upp en knapp för att
lägga till nya regler.

Jobblistor
=======

Under listan med regler så har vi tre listor med gallringsjobb som är
filtrerade utefter status på jobben. **Pågående** visar gallringsjobb som körs
just nu, **Nästa** är jobb som kommer att exekveras och **Avslutade** är jobb
som är klara.

När en regel är kopplad till minst en AIP vars gallringsfrist har utgått så
kommer det skapas ett jobb under **Nästa**. Det jobbet kan vi antingen vänta
på ska exekveras automatiskt vid tiden som står under **Start**. Alternativt
kan vi klicka på **Förhandsgranska** och sedan **Kör** för att exekvera på en
gång. Jobbet kommer då flyttas till **Pågående** och sist **Avslutade**. 

När jobbet är klart och är under **Avslutade** så kan vi klicka på **Rapport**
för att se rapporten för det jobbet.
