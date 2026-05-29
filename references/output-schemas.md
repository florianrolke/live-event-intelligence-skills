# Output Schemas

Event columns:
`event_name,date_start,date_end,venue,city,state,country,category,source,event_url,organizer,organizer_url,cost,tags,description,confidence,evidence`

Contact columns:
`person_name,title,organization,role_type,event_name,segment,email,phone,linkedin_url,facebook_url,instagram_url,website,source,confidence,evidence,next_action`

Association columns:
`association_name,segment,city,state,country,website,event_calendar_url,member_directory_url,linkedin_url,facebook_url,instagram_url,contact_name,contact_title,email,phone,source,confidence,evidence`

LinkedIn match columns:
`name,company,type,linkedin_url,match_confidence,evidence,notes`

Confidence values:
- `confirmed`: exact official/public source match.
- `probable`: strong name/company/title match but not fully verified.
- `weak`: possible match; keep for manual review only.
- `historical-reference`: prior-year or non-current event evidence.
- `needs-manual-verification`: useful but incomplete evidence.