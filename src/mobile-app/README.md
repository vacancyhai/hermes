# Hermes Mobile App (Phase 9)

React Native app — planned for Phase 9 (issues #142–#143).

## What's Already Done

The backend and Firebase configuration are fully ready. No backend changes are needed to start building the app.

| Component | Status | Detail |
|-----------|--------|--------|
| `POST /auth/verify-token` | ✅ Ready | Exchange Firebase ID token for internal JWT (email, Google, phone OTP) |
| `POST /users/me/fcm-token` | ✅ Ready | Register device FCM token after login |
| `DELETE /users/me/fcm-token` | ✅ Ready | Unregister FCM token on logout |
| `firebase_uid` on users | ✅ Ready | DB migration 0009 — unique index |
| Phone-only users | ✅ Ready | DB migration 0010 — `email` nullable |
| Android Firebase config | ✅ Ready | `google-services.json` in this directory |
| iOS Firebase config | ✅ Ready | `GoogleService-Info.plist` in this directory |
| Test phone number | ✅ Ready | `+917777777777` / OTP `123456` in Firebase Console |

## Firebase Config Files

| File | Platform | Package |
|------|----------|---------|
| `google-services.json` | Android | `com.hermes.app` |
| `GoogleService-Info.plist` | iOS | `com.hermes.app` |

Both connect to Firebase project `hermes-7`.

When the React Native project is initialized here:
- Move `google-services.json` → `android/app/google-services.json`
- Move `GoogleService-Info.plist` → `ios/Hermes/GoogleService-Info.plist`

## Firebase Test Credentials (Phone OTP)

| Phone | OTP |
|-------|-----|
| +917777777777 | 123456 |

Configured in Firebase Console → Authentication → Phone numbers for testing.

## Auth Flow (React Native)

```
1. @react-native-firebase/auth sign-in
   (signInWithEmailAndPassword / signInWithPopup / signInWithPhoneNumber)
       ↓
2. auth.currentUser.getIdToken()  →  Firebase ID token
       ↓
3. POST /api/v1/auth/verify-token  { "id_token": "..." }
       →  { "access_token": "...", "refresh_token": "..." }
       ↓
4. Store tokens in react-native-keychain
5. Add Authorization: Bearer <access_token> to all API requests
6. On 401 → POST /api/v1/auth/refresh  →  new token pair
```

## FCM Push Flow (React Native)

```
1. @react-native-firebase/messaging.requestPermission()
2. messaging().getToken()  →  FCM device token
3. POST /api/v1/users/me/fcm-token  { "token": "...", "device_name": "..." }
4. On logout: DELETE /api/v1/users/me/fcm-token  { "token": "..." }
5. messaging().onTokenRefresh(token => re-register)
```

## Remaining Work (Phase 9)

- [ ] Initialize React Native CLI project in `src/mobile-app/`
- [ ] Move Firebase config files into RN project structure
- [ ] Build screens: job listing, job detail, search, dashboard, notifications, profile
- [ ] Implement Firebase Auth sign-in → `POST /auth/verify-token`
- [ ] Implement FCM token registration / unregistration
- [ ] Secure token storage via `react-native-keychain`
- [ ] Axios instance with JWT interceptor (auto-refresh on 401)
