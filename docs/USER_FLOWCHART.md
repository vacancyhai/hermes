# Hermes — User Flowcharts

---

## 1. Overall Site Flow

```
                        ┌─────────────────┐
                        │   User Opens    │
                        │    Website      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Dashboard     │
                        │   (home page)   │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌──────────────┐         ┌──────────────────┐
           │  Already     │   NO    │  Dashboard page  │
           │  Logged In?  │────────▶│  (guest view)    │
           └──────┬───────┘         │                  │
                  │ YES             │  Browse Jobs,    │
                  │                 │  Admissions etc. │
                  │                 │  + [Login] button│
                  │                 └────────┬─────────┘
                  │                          │
                  │                          │  Clicks [Login]
                  │                          ▼
                  │                 ┌──────────────────┐
                  │                 │   Login Page     │
                  │                 │   opens          │
                  │                 └────────┬─────────┘
                  │                          │  Signs in
                  │                          │
                  └──────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────────────────────────┐
                    │   Dashboard page (logged-in view)   │
                    │                                     │
                    │  ┌──────────────────────────────┐  │
                    │  │ 📋 Latest Jobs               │  │
                    │  │ [card][card][card]... ──────▶ │  │
                    │  │                   [View All →]│  │
                    │  └──────────────────────────────┘  │
                    │  ┌──────────────────────────────┐  │
                    │  │ 🎓 Latest Admissions         │  │
                    │  │ [card][card][card]... ──────▶ │  │
                    │  │                   [View All →]│  │
                    │  └──────────────────────────────┘  │
                    │  ┌──────────────────────────────┐  │
                    │  │ 🪪 Latest Admit Cards        │  │
                    │  │ [card][card][card]... ──────▶ │  │
                    │  │                   [View All →]│  │
                    │  └──────────────────────────────┘  │
                    │  ┌──────────────────────────────┐  │
                    │  │ 📝 Latest Answer Keys        │  │
                    │  │ [card][card][card]... ──────▶ │  │
                    │  │                   [View All →]│  │
                    │  └──────────────────────────────┘  │
                    │  ┌──────────────────────────────┐  │
                    │  │ 🏆 Latest Results            │  │
                    │  │ [card][card][card]... ──────▶ │  │
                    │  │                   [View All →]│  │
                    │  └──────────────────────────────┘  │
                    └─────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
           ┌─────────────────┐              ┌─────────────────┐
           │ User scrolls    │              │ User clicks     │
           │ row left/right  │              │ [View All →]    │
           │ to see all 12   │              │ at end of row   │
           │ cards           │              └────────┬────────┘
           └─────────────────┘                       │
                                                      ▼
                                           ┌─────────────────────┐
                                           │ Opens that section's│
                                           │ full list page      │
                                           │                     │
                                           │ Jobs    → /jobs     │
                                           │ Admiss. → /admissions│
                                           │ Admit C → /admit-cards│
                                           │ Ans Key → /answer-keys│
                                           │ Results → /results  │
                                           └─────────────────────┘
```

---

## 2. Sign Up Flow

```
       ┌──────────────────┐
       │   /login page    │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  Click Register  │
       │       tab        │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │ Enter Name +     │
       │ Email            │
       │ → Send OTP       │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  OTP arrives     │
       │  in email inbox  │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐         ┌──────────────────┐
       │  Enter OTP code  │  WRONG  │  Error message   │
       │                  │────────▶│  Try again       │
       └────────┬─────────┘         └──────────────────┘
                │ CORRECT
                ▼
       ┌──────────────────┐
       │  Set Password    │
       │  (min 8 chars)   │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  Account created │
       │  Logged in ✓     │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │   Dashboard      │
       └──────────────────┘
```

---

## 3. Login Flow

```
       ┌──────────────────────────────────────────┐
       │              /login page                 │
       └───────────────────┬──────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │   Google     │ │   Email +    │ │    Phone     │
  │   Sign In    │ │   Password   │ │    OTP       │
  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
         │                │                │
         │         ┌──────┴──────┐  ┌──────┴──────┐
         │         │ Enter email │  │ Enter phone │
         │         │ + password  │  │ number      │
         │         └──────┬──────┘  └──────┬──────┘
         │                │                │
         │                │         ┌──────┴──────┐
         │                │         │ Enter SMS   │
         │                │         │ OTP code    │
         │                │         └──────┬──────┘
         │                │                │
         └────────────────┴────────────────┘
                           │
               ┌───────────┴───────────┐
               │                       │
               ▼                       ▼
       ┌──────────────┐       ┌──────────────────┐
       │  Login OK ✓  │       │  Login Failed ✗  │
       └──────┬───────┘       │  Error shown,    │
              │               │  try again       │
              ▼               └──────────────────┘
       ┌──────────────┐
       │ Go to page   │
       │ they wanted, │
       │ or Dashboard │
       └──────────────┘
```

---

## 4. Browse & Watch a Job

```
       ┌──────────────────┐
       │  Click "Jobs"    │
       │  in navbar       │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  Jobs List page  │
       │  All Jobs tab    │◀─── [Load More] loads next 20
       └────────┬─────────┘
                │
                │  Logged in?
                ├── YES ──▶ [✨ For You] tab also visible
                │           (personalised picks)
                │
                ▼
       ┌──────────────────┐
       │  Click a job     │
       │  "View Details →"│
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │  Job Detail page │
       │                  │
       │  • Key dates     │
       │  • Vacancies     │
       │  • Eligibility   │
       │  • Fee table     │
       │  • Links         │
       └────────┬─────────┘
                │
         ┌──────┴───────────────┐
         │                      │
         ▼                      ▼
  ┌─────────────┐      ┌──────────────────┐
  │ Apply Online│      │ ☆ Watch for      │
  │ (external   │      │   Reminders      │
  │  website)   │      └────────┬─────────┘
  └─────────────┘               │
                      ┌─────────┴─────────┐
                      │                   │
                      ▼                   ▼
               ┌────────────┐    ┌─────────────────┐
               │ Logged In? │ NO │ Go to Login     │
               │            │───▶│ page, then come │
               └─────┬──────┘    │ back here       │
                     │ YES       └─────────────────┘
                     ▼
               ┌────────────┐
               │ ★ Watching │
               │  Job saved │
               │ to watchlist
               └─────┬──────┘
                     │
                     ▼
               ┌────────────┐
               │ Reminders  │
               │ will arrive│
               │ via 🔔     │
               └────────────┘
```

---

## 5. Dashboard (Watchlist) Flow

```
       ┌──────────────────┐
       │ Click "Dashboard"│
       │ in navbar        │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐         ┌──────────────────┐
       │  Logged in?      │   NO    │  Login form      │
       │                  │────────▶│  shown on page   │
       └────────┬─────────┘         └──────────────────┘
                │ YES
                ▼
       ┌──────────────────┐
       │  Dashboard       │
       │  ┌────┐ ┌────┐   │
       │  │ 12 │ │ 8  │   │  ← stats: total watching, jobs, admissions
       │  └────┘ └────┘   │
       └────────┬─────────┘
                │
       ┌────────┴──────────┐
       │                   │
       ▼                   ▼
┌────────────────┐  ┌─────────────────┐
│ Watched Jobs   │  │ Watched         │
│ listed below   │  │ Admissions      │
│                │  │ listed below    │
│ [View →]       │  │ [View →]        │
│ [★ Unwatch]    │  │ [★ Unwatch]     │
└────────────────┘  └─────────────────┘
       │
       │  Nothing watched yet?
       ▼
┌────────────────────────────┐
│  Empty state               │
│  "No items watched yet"    │
│  [Browse Jobs]             │
│  [Browse Admissions]       │
└────────────────────────────┘
```

---

## 6. Notifications Flow

```
       ┌──────────────────────────────────┐
       │  🔔 badge in navbar              │
       │  (updates every 30 seconds)      │
       └─────────────┬────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Badge shows "3" │  ← 3 unread notifications
            └────────┬────────┘
                     │
                     │  User clicks bell
                     ▼
            ┌─────────────────┐
            │ Notifications   │
            │ page opens      │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
 ┌───────────┐ ┌──────────┐ ┌──────────────┐
 │ Click     │ │ Mark     │ │ Delete       │
 │ title to  │ │ read     │ │ notification │
 │ go to     │ │ (removes │ │ permanently  │
 │ that page │ │  blue)   │ └──────────────┘
 └───────────┘ └──────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ [Mark all read] │  ← clears all at once
            └─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ [Load more]     │  ← shows older notifications
            └─────────────────┘
```

---

## 7. Profile Setup Flow

```
       ┌──────────────────┐
       │ Click "Profile"  │
       │ in navbar        │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐         ┌──────────────────┐
       │  Logged in?      │   NO    │  Go to Login     │
       │                  │────────▶│  page            │
       └────────┬─────────┘         └──────────────────┘
                │ YES
                ▼
       ┌──────────────────┐
       │  Profile page    │
       └────────┬─────────┘
                │
       ┌────────┴────────────────────┐
       │                             │
       ▼                             ▼
┌──────────────────┐        ┌─────────────────────┐
│ First visit?     │        │ Returning user      │
│ Amber banner:    │        │ Form pre-filled     │
│ "Profile not     │        │ with saved info     │
│  set up yet"     │        └──────────┬──────────┘
└──────┬───────────┘                   │
       │                               │
       └──────────────┬────────────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Fill in:        │
             │ • Gender/State  │
             │ • Qualification │
             │ • Category      │
             │ • Stream        │
             │ • Orgs to follow│
             │ • Notif prefs   │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Click           │
             │ "Save Profile"  │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ ✓ Green banner: │
             │ "Profile        │
             │  updated."      │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────────────────┐
             │ ✨ For You tabs now active   │
             │ across Jobs, Admissions,    │
             │ Admit Cards, Results        │
             └─────────────────────────────┘
```

---

## 8. Full User Journey (New User → Personalised Experience)

```
  ┌─────────────┐
  │  New User   │
  │  visits site│
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Dashboard  │──── not logged in ────▶ Login form shown
  └──────┬──────┘
         │  (browses without logging in)
         ▼
  ┌─────────────┐
  │  Jobs page  │
  │  (browsing) │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Opens a    │
  │  Job detail │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Clicks      │
  │ ☆ Watch     │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Login page │◀── redirected here
  │  (signs in) │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Back to    │◀── automatically returned
  │  Job detail │
  │  ★ Watching │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Goes to    │
  │  Profile    │
  │  fills info │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Returns to │
  │  Jobs page  │
  │  ✨ For You │◀── personalised tab now shows
  │  tab appears│
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  🔔 Bell    │
  │  lights up  │◀── deadline reminder / new admit card
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │Notification │
  │ page opens  │
  │ clicks link │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Downloads  │
  │  Admit Card │
  │  / Result   │
  └─────────────┘
```
