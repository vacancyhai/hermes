# Hermes — Complete User Flow (ASCII Flowchart)

> Single reference document for UI/UX design.
> All screens, states, branches, and interaction paths in one place.

---

## FLOW 1 — Overall Site Entry

```
                    +-------------------------+
                    |   User opens Website    |
                    |   https://hermes.com    |
                    +------------+------------+
                                 |
                                 v
                    +------------+------------+
                    |    Already Logged In?   |
                    +------+----------+-------+
                           |          |
                          YES         NO
                           |          |
                           |          v
                           |  +-------+---------------------------+
                           |  |   HOME  /  (Guest View)           |
                           |  |                                   |
                           |  |  Navbar:                          |
                           |  |  [Logo][Jobs][Admissions]         |
                           |  |  [Admit Cards][Answer Keys]       |
                           |  |  [Results][Login][Register]       |
                           |  |                                   |
                           |  |  Hero banner + Search bar         |
                           |  |                                   |
                           |  |  Horizontal scroll rows (x5):     |
                           |  |  [Jobs cards ...][View All ->]    |
                           |  |  [Admissions   ...][View All ->]  |
                           |  |  [Admit Cards  ...][View All ->]  |
                           |  |  [Answer Keys  ...][View All ->]  |
                           |  |  [Results      ...][View All ->]  |
                           |  |                                   |
                           |  |  Footer                           |
                           |  +-------+---------------------------+
                           |          |
                           |          | User clicks [Login] or [Register]
                           |          v
                           |  +-------+-------+
                           |  |  /login page  |
                           |  +-------+-------+
                           |          |
                           |    (see FLOW 2 & FLOW 3)
                           |          |
                           +----------+
                                      |
                                      v
              +---------------------------+----------------------------+
              |   HOME  /  (Logged-In View)                         |
              |                                                        |
              |  Navbar:                                               |
              |  [Logo][Jobs][Admissions][Admit Cards]                 |
              |  [Answer Keys][Results][Bell+badge][Profile avatar]    |
              |                                                        |
              |  Same 5 horizontal rows, each card shows:             |
              |  [Title][Org][Deadline badge][Track][Share][Details->] |
              |                                                        |
              |  [View All ->] on each row -> section list page        |
              +---------------------------+----------------------------+
                                          |
              +---------+-----------+-----+------+---------+---------+
              |         |           |            |         |         |
              v         v           v            v         v         v
           /jobs  /admissions /admit-cards /answer-keys /results /my-account
          FLOW 4   FLOW 5      FLOW 6       FLOW 7      FLOW 8   FLOW 9
                                                              (My Account)
                                                 Bell -> /notifications
                                                             FLOW 10
                                                 Avatar -> /profile
                                                             FLOW 11
```

---

## FLOW 2 — Sign Up

```
              +---------------------+
              |    /login page      |
              |  [ Login | Register ]  <- tabs
              +----------+----------+
                         |
                   Click [Register]
                         |
                         v
              +----------+----------+
              |  Enter Name + Email |
              |  Click [Send OTP]   |
              +----------+----------+
                         |
                         v
              +----------+----------+
              |  OTP sent to email  |
              |  inbox              |
              +----------+----------+
                         |
                         v
              +----------+----------+
              |  Enter OTP code     |
              +----+----------+-----+
                   |          |
                 WRONG      CORRECT
                   |          |
                   v          v
          +--------+--+  +----+--------------------+
          | Error msg  |  | Set Password            |
          | [Try Again]|  | (min 8 chars,           |
          +--------+--+  |  1 uppercase, 1 special) |
               |         +----+--------------------+
               |              |
               +--(loop back) |
                              v
                   +----------+----------+
                   | Account created  v  |
                   | Auto-login           |
                   +----------+----------+
                              |
                              v
                   +----------+----------+
                   |  HOME  /  (logged)  |
                   +---------------------+
```

---

## FLOW 3 — Login

```
              +---------------------------------------------+
              |               /login page                   |
              +-------+----------------+--------------------+
                      |                |                    |
                      v                v                    v
              +-------+------+ +-------+------+  +---------+------+
              | Google       | | Email +      |  | Phone OTP      |
              | Sign In      | | Password     |  |                |
              +-------+------+ +-------+------+  +---------+------+
                      |                |                    |
                      | OAuth flow     | Enter email        | Enter phone
                      |                | + password         | number
                      |                |                    |
                      |                |                    v
                      |                |          +---------+------+
                      |                |          | Enter SMS OTP  |
                      |                |          | code           |
                      |                |          +---------+------+
                      |                |                    |
                      +--------+-------+--------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
      +--------+-------+             +---------+--------+
      | LOGIN OK  (v)  |             | LOGIN FAILED (x) |
      +--------+-------+             | Error shown      |
               |                     | [Try Again]      |
               v                     +---------+--------+
      +--------+--------------------+          |
      | Redirect to:                |          | (loop back to form)
      |  - Originally requested page|
      |  - OR Home  /               |
      +-----------------------------+
```

---

## FLOW 4 — Jobs

```
              +-----------------------------+
              |  Click "Jobs" in navbar     |
              |  OR [View All ->] on dash   |
              +-------------+---------------+
                            |
                            v
              +-------------+-------------------------------------+
              |   JOBS LIST  /jobs                                |
              |                                                   |
              |  Hero: "Government Jobs" (Navy -> Blue)           |
              |  [ Search bar — live, 300ms debounce ]           |
              |  Filters: [State][Category][Post Type][Qual.]     |
              |                                                   |
              |  Tabs:  [ All Jobs ] | [ For You (*) ]           |
              |         (*) requires profile; else amber banner   |
              |             "Complete your profile -> /profile"   |
              |                                                   |
              |  Job Card (repeats, Load More = 20/page):         |
              |  +-------------------------------------------+   |
              |  | [Navy accent] Title   Org   Post badge     |   |
              |  |  Apply end: DD MMM   Exam: DD MMM          |   |
              |  |  Vacancies: NNN   Salary: X-Y LPA          |   |
              |  |  [Track] [Share] [View Details ->]         |   |
              |  +-------------------------------------------+   |
              +-------------+-------------------------------------+
                            |
                    Click [View Details ->]
                            |
                            v
              +-------------+-------------------------------------+
              |   JOB DETAIL  /jobs/{slug}                        |
              |                                                   |
              |  Hero: Job Title + Org  (Navy -> Blue)  [Share]  |
              |                                                   |
              |  Info sections:                                   |
              |  +- Key Dates --------------------------------+   |
              |  |  Application: Start ~ End                  |   |
              |  |  Exam: Start ~ End  |  Result: Date        |   |
              |  +--------------------------------------------+   |
              |  +- Vacancies table (category-wise) ----------+   |
              |  +- Eligibility (Age / Education / Nation.) --+   |
              |  +- Fee table (Gen/OBC/SC/ST/EWS/PH) ---------+   |
              |  |  "Your fee: Rs X" (if profile set) --------+   |
              |  +- Selection Process -------------------------+   |
              |  +- Links: [Apply Online] [Official PDF] ------+   |
              |                                                   |
              |  Action buttons:                                  |
              |  [Apply Online -> external site]                  |
              |  [Track for Reminders]                            |
              |                                                   |
              |  Document tabs (HTMX loaded):                     |
              |  [Admit Cards] [Answer Keys] [Results]            |
              +--+------------------+-----------------------------+
                 |                  |
                 v                  v
        +--------+------+  +--------+--------------------------+
        | [Apply Online]|  | [Track for Reminders]            |
        | -> external   |  +----+------------------+----------+
        |   site (tab)  |       |                  |
        +---------------+  Logged In?            NOT logged in
                                |                  |
                               YES                 v
                                |        +---------+---------+
                                v        | /login page       |
                       +--------+------+ | (redirect back    |
                       | TRACKING (*)  | |  after login)     |
                       | saved to      | +---------+---------+
                       | tracker     |           |
                       +--------+------+           | signs in
                                |                  |
                                v                  v
                       +--------+------------------+------+
                       | Reminders via Bell notifications  |
                       | T-7, T-3, T-1 before deadline     |
                       +-----------------------------------+
```

---

## FLOW 5 — Admissions

```
              +-----------------------------+
              |  Click "Admissions" navbar  |
              |  OR [View All ->] on dash   |
              +-------------+---------------+
                            |
                            v
              +-------------+-------------------------------------+
              |   ADMISSIONS LIST  /admissions                    |
              |                                                   |
              |  Hero: "Admissions" (Dark Purple -> Purple)       |
              |  [ Search bar — live, HTMX ]                     |
              |  Filters: [State][Level: UG/PG/PhD][Stream]       |
              |                                                   |
              |  Tabs:  [ All Admissions ] | [ For You (*) ]     |
              |                                                   |
              |  Admission Card (repeats, Load More):             |
              |  +-------------------------------------------+   |
              |  | [Purple accent] Title   Institution        |   |
              |  |  Stream   Last Apply: DD MMM               |   |
              |  |  [Track] [Share] [View Details ->]         |   |
              |  +-------------------------------------------+   |
              +-------------+-------------------------------------+
                            |
                    Click [View Details ->]
                            |
                            v
              +-------------+-------------------------------------+
              |   ADMISSION DETAIL  /admissions/{slug}            |
              |                                                   |
              |  Hero: Title + Institution  (Purple)  [Share]    |
              |                                                   |
              |  Info sections:                                   |
              |  +- Key Dates (Application window, Adm. Date) -+ |
              |  +- Seats / Intake table ----------------------+ |
              |  +- Eligibility (qualification, age, marks) ---+ |
              |  +- Fee structure -----------------------------+ |
              |  +- Admission Pattern / Counselling process ---+ |
              |  +- Links: [Apply Online] [Prospectus PDF] ----+ |
              |                                                   |
              |  [Track for Reminders]  (same guard as Jobs)      |
              |                                                   |
              |  Document tabs (HTMX loaded):                     |
              |  [Admit Cards] [Answer Keys] [Results]            |
              +---------------------------------------------------+
                  (Track guard -> same as FLOW 4 Track branch)
```

---

## FLOW 6 — Admit Cards

```
              +--------------------------------+
              |  Click "Admit Cards" navbar   |
              |  OR [View All ->] on dash      |
              +--------------+-----------------+
                             |
                             v
              +--------------+----------------------------------+
              |   ADMIT CARDS LIST  /admit-cards                |
              |                                                 |
              |  Hero: "Admit Cards" (Sky Blue)                 |
              |  [ Search bar ] Filters: [Exam][Org][Date]      |
              |                                                 |
              |  Admit Card Item (repeats, [Load More]):        |
              |  +------------------------------------------+  |
              |  |  Exam name   Organization                 |  |
              |  |  Linked: [Job badge] or [Admission badge] |  |
              |  |  Download window: Start - End             |  |
              |  |  [Download ->] (external URL, new tab)    |  |
              |  |  [Share]                                  |  |
              |  +------------------------------------------+  |
              +-------------------------------------------------+
```

---

## FLOW 7 — Answer Keys

```
              +--------------------------------+
              |  Click "Answer Keys" navbar   |
              |  OR [View All ->] on dash      |
              +--------------+-----------------+
                             |
                             v
              +--------------+----------------------------------+
              |   ANSWER KEYS LIST  /answer-keys                |
              |                                                 |
              |  Hero: "Answer Keys" (Brown -> Amber)           |
              |  [ Search bar ] Filters: [Exam][Org][Date]      |
              |                                                 |
              |  Answer Key Item (repeats, [Load More]):        |
              |  +------------------------------------------+  |
              |  |  Exam name   Organization                 |  |
              |  |  Linked: [Job badge] or [Admission badge] |  |
              |  |  Released: DD MMM YYYY                    |  |
              |  |  [Download ->] (external URL, new tab)    |  |
              |  |  [Share]                                  |  |
              |  +------------------------------------------+  |
              +-------------------------------------------------+
```

---

## FLOW 8 — Results

```
              +--------------------------------+
              |  Click "Results" navbar       |
              |  OR [View All ->] on dash      |
              +--------------+-----------------+
                             |
                             v
              +--------------+----------------------------------+
              |   RESULTS LIST  /results                        |
              |                                                 |
              |  Hero: "Results" (Dark Green -> Green)          |
              |  [ Search bar ] Filters: [Exam][Org][Date]      |
              |                                                 |
              |  Result Item (repeats, [Load More]):            |
              |  +------------------------------------------+  |
              |  |  Exam name   Organization                 |  |
              |  |  Linked: [Job badge] or [Admission badge] |  |
              |  |  Result Date: DD MMM YYYY                 |  |
              |  |  [View Result ->] (external URL, new tab) |  |
              |  |  [Share]                                  |  |
              |  +------------------------------------------+  |
              +-------------------------------------------------+
```

---

## FLOW 9 — My Account (Tracker)

```
              +-----------------------------------+
              |  Click "My Account" in navbar     |
              +----------------+------------------+
                               |
                               v
              +----------------+------------------+
              |  Logged In?                        |
              +------+----------------------------++
                     |                    |
                    YES                   NO
                     |                   |
                     |                   v
                     |      +-----------+-----------+
                     |      | Login form shown      |
                     |      | on page / redirect    |
                     |      +-----------+-----------+
                     |                  |
                     |           signs in
                     |                  |
                     +------------------+
                                        |
                                        v
              +-------------------------+---------------------+
              |   MY ACCOUNT  /my-account                     |
              |                                               |
              |  Stats: [Total: 12]  [Jobs: 8]  [Adm: 4]     |
              |                                               |
              |  +-- Tracked Jobs -------------------------+  |
              |  |  Title  |  Org  |  Deadline             |  |
              |  |  [View ->]      |  [Untrack (*)]        |  |
              |  |  (repeats for each tracked job)         |  |
              |  +-----------------------------------------+  |
              |                                               |
              |  +-- Tracked Admissions -------------------+  |
              |  |  Title  |  Institution  |  Deadline     |  |
              |  |  [View ->]              |  [Untrack (*)]|  |
              |  |  (repeats for each tracked admission)   |  |
              |  +-----------------------------------------+  |
              |                                               |
              |  Empty state (nothing tracked yet):           |
              |  "No items tracked yet."                      |
              |  [Browse Jobs ->]   [Browse Admissions ->]    |
              +-----------------------------------------------+
                     |                        |
               [View ->] Job          [View ->] Admission
                     |                        |
                     v                        v
           /jobs/{slug}              /admissions/{slug}
           (FLOW 4 detail)           (FLOW 5 detail)
```

---

## FLOW 10 — Notifications

```
              +---------------------------------------------+
              |   Bell icon in Navbar                       |
              |   Badge updates every 30 s (HTMX poll)      |
              |                                             |
              |   Badge states:                             |
              |     0 unread  -> no badge shown             |
              |     1-9 unread -> red badge "N"             |
              |     10+ unread -> red badge "9+"            |
              +-------------------+-------------------------+
                                  |
                        User clicks Bell
                                  |
                                  v
              +-------------------+-------------------------+
              |   NOTIFICATIONS PAGE  /notifications        |
              |                                             |
              |   [ Mark All Read ]                         |
              |                                             |
              |   Notification item (repeats):              |
              |   +--------------------------------------+  |
              |   |  [Blue dot = unread]                 |  |
              |   |  Title (clickable link)              |  |
              |   |  Body text                           |  |
              |   |  Timestamp                           |  |
              |   |  [Mark Read]  [Delete]               |  |
              |   +--------------------------------------+  |
              |                                             |
              |   [ Load More ] -> older notifications      |
              +-----+---------------------+----------------++
                    |                     |
          Click Title link         [Mark Read]        [Delete]
                    |                     |                |
                    v                     v                v
           +--------+---------+   Blue dot removed   Removed
           | Target page:     |   from that item     permanently
           | /jobs/{slug}     |
           | /admissions/{slug}
           | /admit-cards     |
           | /answer-keys     |
           | /results         |
           +------------------+

    Notification types delivered:
    +-----------------------------------------------------------+
    |  Type                    | Trigger                        |
    |--------------------------|--------------------------------|
    |  Deadline reminder       | T-7, T-3, T-1 before close    |
    |  New Admit Card          | Published for tracked item     |
    |  New Answer Key          | Published for tracked item     |
    |  New Result              | Published for tracked item     |
    |  Status update           | Tracked job/admission updated  |
    |  Welcome                 | On first registration          |
    +-----------------------------------------------------------+

    Delivery channels (set in Profile):
    +-----------------------------------------------------------+
    |  Channel   | Mode      | Timing                          |
    |------------|-----------|----------------------------------|
    |  In-app    | Instant   | T+0  (always on)               |
    |  Push/FCM  | Instant   | T+0  (needs PWA/mobile)        |
    |  Email     | Staggered | T+15 min (default)             |
    |  Telegram  | Staggered | T+15 min (user sets chat_id)   |
    |  WhatsApp  | Staggered | T+1 hr   (placeholder only)    |
    +-----------------------------------------------------------+
```

---

## FLOW 11 — Profile Setup

```
              +-----------------------------------+
              |  Click "Profile" / avatar         |
              |  in navbar                        |
              +-----------------+-----------------+
                                |
                                v
              +-----------------+-----------------+
              |  Logged In?                        |
              +--------+--------------------------++
                       |                   |
                      YES                  NO
                       |                   |
                       |                   v
                       |      +------------+------+
                       |      | Redirect to /login |
                       |      +--------------------+
                       |
                       v
              +--------+----------------------------------+
              |   PROFILE PAGE  /profile                  |
              +--------+------------------+---------------+
                       |                  |
               First visit?         Returning user?
                       |                  |
                       v                  v
              +--------+------+  +--------+--------------+
              | Amber banner: |  | Form pre-filled with  |
              | "Profile not  |  | saved data            |
              | set up yet"   |  +--------+--------------+
              +--------+------+           |
                       |                  |
                       +--------+---------+
                                |
                                v
              +-----------------+-------------------------------+
              |  Profile Form                                    |
              |                                                  |
              |  Personal info:                                  |
              |  [ Gender (dropdown) ]                           |
              |  [ State (dropdown) ]                            |
              |  [ Highest Qualification (dropdown) ]            |
              |  [ Category: Gen / OBC / SC / ST / EWS / PH ]   |
              |  [ Stream: Science/Commerce/Arts/Engg/etc. ]     |
              |                                                  |
              |  Organizations to follow (multi-select):         |
              |  [ SSC ] [ UPSC ] [ Railway ] [ Banking ] ...   |
              |                                                  |
              |  Notification Preferences:                       |
              |  [ Email   ON/OFF toggle ]                       |
              |  [ Push    ON/OFF toggle ]                       |
              |  [ Telegram chat_id  (text input) ]              |
              |  [ WhatsApp number   (text input) ]              |
              |                                                  |
              |  [ Save Profile ]                                |
              +-----------------+-------------------------------+
                                |
                                v
              +-----------------+-------------------------------+
              |  Green banner: "Profile updated."               |
              +-----------------+-------------------------------+
                                |
               +----------------+----------------+
               |                                 |
               v                                 v
    "For You" tabs now active         Fee table on Job/Admission
    across all 5 sections             detail shows "Your fee: Rs X"
    (Jobs, Admissions,                based on saved Category
     Admit Cards, Results)
```

---

## FLOW 12 — Full New-User Journey (End-to-End Happy Path)

```
    +--------------------+
    | New User           |
    | visits site        |
    +--------+-----------+
             |
             v
    +--------+-----------+
    | Home (guest)       |
    | browses without    |
    | logging in         |
    +--------+-----------+
             |
             v
    +--------+-----------+
    | Jobs list  /jobs   |
    | browses job cards  |
    +--------+-----------+
             |
             v
    +--------+-----------+
    | Opens Job Detail   |
    | /jobs/{slug}       |
    +--------+-----------+
             |
             v
    +--------+-----------+
    | Clicks [Track]     |
    | (not logged in)    |
    +--------+-----------+
             |
             v
    +--------+-----------+
    | Redirected to      |
    | /login page        |
    | Signs in / up      |
    +--------+-----------+
             |
             v
    +--------+---------------------+
    | Returned to /jobs/{slug}     |
    | Star icon now filled         |
    | "You are tracking this job"  |
    +--------+---------------------+
             |
             v
    +--------+-----------+
    | Goes to /profile   |
    | fills in:          |
    | Category, State,   |
    | Qualification,     |
    | Stream, Orgs       |
    | Saves profile      |
    +--------+-----------+
             |
             v
    +--------+---------------------+
    | Returns to /jobs             |
    | "For You" tab appears        |
    | Personalised job picks shown |
    +--------+---------------------+
             |
             v
    +--------+-------------------------------------+
    | Bell icon lights up (unread badge)           |
    | (deadline reminder OR new admit card         |
    |  published for tracked job)                  |
    +--------+-------------------------------------+
             |
             v
    +--------+-----------+
    | Opens              |
    | /notifications     |
    | clicks title link  |
    +--------+-----------+
             |
             v
    +--------+---------------------+
    | /admit-cards  OR  /results   |
    | Downloads Admit Card         |
    | Views Result                 |
    +------------------------------+
```

---

## Card UI States (All Sections)

```
    +----------------------------------------------+
    |  STATE           VISUAL TREATMENT             |
    +----------------------------------------------+
    |  Default       | White bg, left accent border |
    |                | in section colour            |
    +----------------+------------------------------+
    |  Tracked       | Filled star icon             |
    |                | Subtle tinted background     |
    +----------------+------------------------------+
    |  Deadline <=3d | Red badge "X days left"      |
    +----------------+------------------------------+
    |  Closed /      | Grey card, "Closed" badge    |
    |  Expired       | [Track] button hidden        |
    +----------------+------------------------------+
    |  Loading       | Skeleton / shimmer           |
    |  (HTMX fetch)  | placeholder                  |
    +----------------+------------------------------+
    |  Empty list    | Illustration + message       |
    |                | + CTA button                 |
    +----------------------------------------------+
```

---

## Screen Inventory

```
    +----+------------------------+----------------------+-------+
    | #  | Screen                 | URL                  | Auth  |
    +----+------------------------+----------------------+-------+
    |  1 | Home (Guest)           | /                    | No    |
    |  2 | Login / Register       | /login               | No    |
    |  3 | Home (Logged In)       | /                    | Yes   |
    |  4 | Jobs List              | /jobs                | No *  |
    |  5 | Job Detail             | /jobs/{slug}         | No *  |
    |  6 | Admissions List        | /admissions          | No *  |
    |  7 | Admission Detail       | /admissions/{slug}   | No *  |
    |  8 | Admit Cards List       | /admit-cards         | No    |
    |  9 | Answer Keys List       | /answer-keys         | No    |
    | 10 | Results List           | /results             | No    |
    | 11 | Notifications          | /notifications       | Yes   |
    | 12 | Profile                | /profile             | Yes   |
    | 13 | My Account             | /my-account          | Yes   |
    | 14 | Offline fallback       | /offline             | No    |
    +----+------------------------+----------------------+-------+
     * = page public; Track action + "For You" tab require login
```

---

## Section Colour Reference

```
    +----------------+----------------------+-------------------+
    | Section        | Hero Gradient        | Card Accent       |
    +----------------+----------------------+-------------------+
    | Jobs           | Navy  ->  Blue       | Navy              |
    | Admissions     | Dark Purple -> Purple| Purple            |
    | Admit Cards    | Sky Blue (flat)      | Sky Blue          |
    | Answer Keys    | Brown -> Amber       | Amber             |
    | Results        | Dark Green -> Green  | Green             |
    +----------------+----------------------+-------------------+
```
