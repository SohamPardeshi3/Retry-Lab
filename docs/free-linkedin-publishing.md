# Free LinkedIn publishing setup

RetryLab can schedule an explicitly approved LinkedIn personal-profile post through Buffer's free plan and public API. Buffer's Free plan currently includes API access (one API key; 3,000 requests per 30 days) and up to 10 scheduled posts per connected channel. Check Buffer's current pricing and API documentation before relying on these limits.

## One-time setup

1. Create a free account at https://buffer.com/pricing.
2. Connect your **personal LinkedIn profile** in Buffer and confirm it can publish automatically.
3. Open Buffer's API settings and create a personal API key: https://publish.buffer.com/settings/api.
4. In Buffer's API Explorer, run this query to get your organization ID:

   ```graphql
   query {
     account {
       organizations {
         id
         name
       }
     }
   }
   ```

5. Use the organization ID in this query to find the LinkedIn channel ID:

   ```graphql
   query Channels($organizationId: OrganizationId!) {
     channels(input: { organizationId: $organizationId }) {
       id
       name
       descriptor
       service { name }
       type
     }
   }
   ```

   Select the channel whose service is `linkedin` and whose type is a personal profile.

6. In this GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `BUFFER_API_KEY`: your Buffer API key
   - `BUFFER_LINKEDIN_CHANNEL_ID`: the personal LinkedIn channel ID from step 5

   Never put the API key in a commit, issue, or chat message.

## How to publish after review

1. Prepare the post text and get approval in the ChatGPT conversation.
2. Open **Actions → Approved LinkedIn Publisher → Run workflow** in this repository.
3. Paste the exact approved text, set the future publish time as ISO 8601 including timezone (for example `2026-10-16T09:00:00+05:30`), and explicitly check **I approve scheduling this exact post**.
4. The workflow sends it to Buffer for automatic publishing at that time. If approval is false, the workflow stops without sending anything.

This is a deliberate second approval gate: the scheduled workflow never runs on a timer and cannot publish unless you manually run it with approval set to true. This automation is only for your own LinkedIn posts; it does not like, comment on, or engage with other people's posts.
