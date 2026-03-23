# Hermes Mobile App (Phase 9)

React Native app — planned for Phase 9.

## Firebase Config Files

| File | Platform | Package |
|------|----------|---------|
| `google-services.json` | Android | `com.hermes.app` |
| `GoogleService-Info.plist` | iOS | `com.hermes.app` |

Both connect to Firebase project `hermes-7`.

When the React Native project is initialized:
- Move `google-services.json` → `android/app/google-services.json`
- Move `GoogleService-Info.plist` → `ios/Hermes/GoogleService-Info.plist`

## Firebase Test Credentials (Phone OTP)

| Phone | OTP |
|-------|-----|
| +917777777777 | 123456 |

Configured in Firebase Console → Authentication → Phone numbers for testing.
