# Log-in

## Functional description

1. Add log-in functionality. When opening app for the first time the user should be greeted with option to:
    - Create account/log-in with google
    - Continue as guest
2. For google log-in we should use standard third party login flow
3. For continue as guest, add information that progress might be lost and will not be avaiable on another device
4. For both "continue as guest" and google log-in allow user to provide his name in pokemon style.
   - Save the user name in his user session data 
5. One home page (index.html) greet the user with his name

## Implementation Plan

### 1. Backend Authentication Implementation

#### 1.1 Set up Firebase Authentication
- Configure Firebase Authentication in the Firebase console to enable Google Sign-In
- Update firebase-credentials.json to include Authentication configuration

#### 1.2 Create Authentication Module
- Create a new module `src/app/auth/auth.py` for authentication logic
- Implement Firebase Authentication integration
- Create functions for:
  - Google sign-in flow
  - Guest user creation
  - User session management
  - Storing user-provided name

#### 1.3 Session Management Updates
- Modify existing session manager to store user authentication data
- Add functions to store/retrieve user's name
- Enhance user ID generation to support both authenticated and guest users

#### 1.4 Create User Data Model
- Create a user data model to store:
  - User ID
  - Authentication type (Google or Guest)
  - User-provided name
  - User preferences and settings

### 2. Frontend Implementation

#### 2.1 Create Login Page
- Create `src/templates/login.html` with:
  - Welcome message and app description
  - Google Sign-In button (using Firebase Auth UI)
  - "Continue as Guest" option
  - Information about guest limitations

#### 2.2 Create Name Input Page
- Create `src/templates/name_input.html` with:
  - Simple input field for user to enter their name
  - Pokemon-style descriptive text (e.g., "Enter your trainer name!")
  - Submit button to save name preference

#### 2.3 Update Landing Page (index.html)
- Modify index.html to include personalized greeting
- Display user's name
- Add logout/switch user option

#### 2.4 Update Base Template
- Add user authentication status to base.html
- Update navigation to include login/logout options
- Add user profile link in header

### 3. Routes and API Implementation

#### 3.1 Authentication Routes
- Add new authentication-related routes to the existing `src/app/app.py` file:
  - `/login` route to display login options
  - `/auth/google` route for Google authentication callback
  - `/auth/guest` route for guest login
  - `/logout` route for sign out

#### 3.2 Name Management Route
- Add `/name` route for name input
- Add `/api/save-name` endpoint to save name

#### 3.3 Session Management Routes
- Add API routes for session management
- Implement middleware to check authentication status

### 4. Security and Deployment

#### 4.1 Security Review
- Audit authentication flow for vulnerabilities
- Ensure proper session management
- Implement CSRF protection

#### 4.2 Deployment Updates
- Update deployment configuration for Firebase Authentication
- Add necessary environment variables

## Manual Actions Required (To be completed by the user)

1. **Firebase Configuration**:
   - Create or update a Firebase project in the Firebase Console
   - Enable Google Sign-In in the Authentication section
   - Generate and download a new firebase-credentials.json file with Auth settings
   - Place the updated credentials file in the project root

2. **Environment Variables**:
   - Set up any required environment variables for Firebase Authentication
   - Update deployment environment variables if deploying to cloud

3. **Google OAuth Setup**:
   - Configure OAuth consent screen in Google Cloud Console
   - Add authorized domains for the application
   - Set up authorized redirect URIs for authentication callbacks

4. **Testing**:
   - Test the authentication flow with a Google account
   - Verify guest login functionality
   - Ensure data persistence works correctly for both authenticated and guest users