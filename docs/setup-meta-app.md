# Setting up a Meta app and access tokens

facebook-mcp talks to the [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
on your behalf, so it needs a Meta app and an access token. You only do this once.

## 1. Create a Meta app

1. Go to <https://developers.facebook.com/apps> and click **Create app**.
2. Choose the **"Manage everything on your Page"** use case (or the
   *Business* app type, depending on what the wizard offers).
3. Open **App settings → Basic** and note the **App ID** and **App secret**.
4. Recommended: under **App settings → Advanced**, turn on
   **Require App Secret**. A stolen token is then useless without the secret,
   which facebook-mcp uses to sign every request (`appsecret_proof`).

You can manage Pages you have a role on while the app is in development mode.
You only need App Review and Advanced Access to manage Pages owned by people
who have no role on your app.

## 2. Generate a user access token

1. Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your app under **Meta App**, and **User Token** under
   **User or Page**.
3. Add these permissions:

   | Permission | Needed for |
   |---|---|
   | `pages_show_list` | Discovering your Pages |
   | `pages_read_engagement` | Reading posts and engagement counts |
   | `pages_read_user_content` | Reading comments |
   | `pages_manage_posts` | Creating, editing and deleting posts |
   | `pages_manage_engagement` | Replying to, hiding and deleting comments |
   | `read_insights` | The insights tools |
   | `business_management` | Pages owned through a Business portfolio |

4. Click **Generate Access Token** and approve the Pages you want to manage.

This token expires in about an hour. Make it long-lived:

```bash
export FB_APP_SECRET=your-app-secret
uvx facebook-mcp exchange-token --app-id YOUR_APP_ID --token SHORT_LIVED_TOKEN
```

The command prints a **long-lived user token**, valid for about 60 days.

## 3. Choose a credential mode

### Multi-page (recommended)

Set `FB_USER_ACCESS_TOKEN` to the long-lived user token. On first use, the
server calls `/me/accounts` to discover every Page you approved, along with each
Page's own token. Call the `list_pages` tool to see them. Set `FB_DEFAULT_PAGE`
to save typing.

When the user token expires (about 60 days), generate and exchange a new one.

### Single page (tokens that never expire)

Page tokens derived from a long-lived user token **do not expire**:

```bash
curl "https://graph.facebook.com/v26.0/me/accounts?fields=id,name,access_token&access_token=LONG_LIVED_USER_TOKEN"
```

Pick your Page from the response and set `FB_PAGE_ID` and
`FB_PAGE_ACCESS_TOKEN`. The token stops working only if you change your
password, remove the app, or lose your role on the Page.

### Production / teams: System User tokens

For servers that run unattended, create a **System User** in
[Business Settings](https://business.facebook.com/settings/system-users),
assign it your Pages and app, and generate a token with the permissions above.
System User tokens can be set to never expire, and they aren't tied to any one
person's account. Use one as `FB_USER_ACCESS_TOKEN`.

## Troubleshooting

| Error message | Fix |
|---|---|
| `The access token is invalid or expired` (code 190) | Generate and exchange a new token. |
| `The token lacks a required permission` (code 10 / 200–299) | Re-generate the token with the missing permission from the table above. |
| `Several Pages are available` | Pass `page` in the request, or set `FB_DEFAULT_PAGE`. |
| `Invalid appsecret_proof` | `FB_APP_SECRET` doesn't belong to the app that issued the token. |
| An insights metric is rejected | Meta renames metrics from time to time. Pass current names through the `metrics` argument. |
