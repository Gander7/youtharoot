# Feature Flags

- Temporary Flags must have an expiry. This should be set 30.
- naming convention
    - default features to off, in case config server goes down
    - prefix of `temp` for any flags that will expire
    - Kinds of Flags
        - `release` for progressive release of a new feature
        - `kill-switch` vKill switch flags are permanent safety mechanisms used to shut off functionality or third-party tools in an emergency.
        - `experiment`, `use-new` for A/B testing or experimental features or to see how a feature works that you might not keep.
        - `migration` for data/system migration like deploying, then waiting for a new table to be created in the db, before flipping it on.
        - `show`, `configure`, etc. Permanent operation flags that control the behaviour of the application, like API timeouts or showing certain warnings.
        - `allow`. Entitlement flags are long-lived operational flags that control whether or not an action is allowed or denied, or whether a user has access to a particular feature.
    - You should be able to read a feature like a sentence, like
        - “Rollout: a new feature”
        - “Configure: a setting”
        - “Allow: an action”
        - “Enable: an entitlement”
        - “Show: an offer”

## Considerations for Later
- Rollouts, percentage based


## Lesson
- How are we doing?
- “Have you ever believed something just because everyone seemed to agree on it?”
- Merge into Citadel High. 
    Judgement because other people dont' agree with me
- 
- Trust/Temptation/Cries of Trust me.
- Disciples paths. They did go