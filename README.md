insta-api
===

Uses Instagram media api to get the latest posts.
Stores long-term tokens in S3 and refreshes once a week.

Note: you will most likely want to add authentication!

Setup
---

- Create an instagram application and get the client id and secret.
  See [docs](https://developers.facebook.com/docs/instagram-basic-display-api)
- Add those to `secrets.yml`, see the example file for format
- Deploy, possibly changing things like region or name first
- Add the url to authorize endpoint to your application's "Valid OAuth Redirect URIs"
- Add yourself as a tester in the application (unless in production)
- Accept the tester request in [your account](https://www.instagram.com/accounts/manage_access/)
- Navigate to the authorize endpoint, it should redirect you
- If you see status ok, you succeeded

Usage
---

Use something like:

    curl https://.../load?user_id=...

to get the latest posts. The refresh lambda will refresh the access token weekly.

If you actually use this for real, you can subscribe to the errors topic.
That way you can take action if a token stops working.

**Note**: there is no authorization in this setup. You may want to:

- Take down the authorize endpoint after setup if only using one account.
    (Just remove that part from serverless.yml)
- Add authorization to the load endpoint or limit callers by e.g. ip.
    (Exercise for the reader.)

**Note 2**: there is no locking, so a busy application could have conflicting
authorization calls and misplace tokens. I only use this for a couple of
accounts that I set up in order (and un-deployed the endpoint).
