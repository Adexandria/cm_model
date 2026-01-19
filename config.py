
"""Configuration file for category definitions used in content moderation."""
LLM_CATEGORIES =  ['hate speech', 
               'dangerous individuals and organisations',
                 'violence and incitement', 
                 'adult nudity and sexual activity',
                   'coordinating harm and publicising crime',
                     'regulated goods', 
                     'bullying and harassment', 
                     'violent and graphic content', 
                     'sexual solicitation', 
                     'manipulated media', 
                     'health, misinformation, safety',
                       'safety, violence, war and conflict', 
                       'cruel and insensitive', 
                       'policy advisory – journalism, marginalised communities', 
                       'violence and insightment',
                         'human exploitation', 
                         'violence and graphic content', 
                         'freedom of expression, humour, politics', 
                         'suicide and self-injury', 
               'lbgt, sex and gender equality', 
               'sexual exploitation of adults',
                 'none',
                   'policy advisory'],

CATEGORIES = [
    "hate speech",
    "violence",
    "incitement",
    "graphic content",
    "dangerous individuals",
    "organisations",
    "other",
    "nudity & sexual activity",
    "regulated goods",
    "bullying & harassment"
]

FIELDS = {
    "case_name":"Case name",
    "summary":"Summary",
    "FB_category":"FB category",
    "summary_issue":"summary / issue",
    "category":"category",
    "full_abstract":"full abstract"
}
ALLOWED_FILE_TYPES = ["csv", "xlsx", "xls"]
DANGEROUS_PREFIXES = ("=", "+", "-", "@")