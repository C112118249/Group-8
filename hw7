erDiagram

    User {
        int user_id PK
        string username
        string discriminator
    }

    Meeting {
        int meeting_id PK
        datetime start_time
        datetime end_time
    }

    AudioFile {
        int audiofile_id PK
        int meeting_id FK
        int user_id FK
        string file_path
        float duration
    }

    Transcript {
        int transcript_id PK
        int audiofile_id FK
        text content
    }

    MeetingParticipant {
        int meeting_id FK
        int user_id FK
        string role
    }

    SpeakerSegment {
        int segment_id PK
        int transcript_id FK
        int user_id FK
        float start_sec
        float end_sec
        text segment_text
    }

    User ||--o{ AudioFile : "說話產生"
    User ||--o{ MeetingParticipant : "參與"
    Meeting ||--o{ MeetingParticipant : "包含參與者"
    Meeting ||--o{ AudioFile : "包含音檔"
    AudioFile ||--o{ Transcript : "產生逐字稿"
    Transcript ||--o{ SpeakerSegment : "拆成片段"
    User ||--o{ SpeakerSegment : "該片段的說話者"
