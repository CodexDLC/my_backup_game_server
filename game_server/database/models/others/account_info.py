from ..models import Base

class AccountInfo(Base):
    __tablename__ = 'account_info'
    __table_args__ = (
        PrimaryKeyConstraint('account_id', name='account_info_pkey'),
        UniqueConstraint('discord_id', name='account_info_discord_id_key'),
        UniqueConstraint('email', name='account_info_email_key'),
        UniqueConstraint('game_id', name='account_info_game_id_key'),
        UniqueConstraint('google_id', name='account_info_google_id_key'),
        UniqueConstraint('steam_id', name='account_info_steam_id_key'),
        UniqueConstraint('telegram_id', name='account_info_telegram_id_key'),
        UniqueConstraint('twitch_id', name='account_info_twitch_id_key'),
        UniqueConstraint('twitter_id', name='account_info_twitter_id_key'),
        UniqueConstraint('username', name='account_info_username_key')
    )

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(50), server_default=text("'website'::character varying"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'active'::character varying"))
    role: Mapped[str] = mapped_column(String(20), server_default=text("'user'::character varying"))
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    username: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(Text)
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    google_id: Mapped[Optional[str]] = mapped_column(Text)
    discord_id: Mapped[Optional[str]] = mapped_column(Text)
    telegram_id: Mapped[Optional[str]] = mapped_column(Text)
    twitter_id: Mapped[Optional[str]] = mapped_column(Text)
    steam_id: Mapped[Optional[str]] = mapped_column(Text)
    twitch_id: Mapped[Optional[str]] = mapped_column(Text)
    game_id: Mapped[Optional[int]] = mapped_column(Integer)
    linked_platforms: Mapped[Optional[str]] = mapped_column(Text)
    auth_token: Mapped[Optional[str]] = mapped_column(Text)
    avatar: Mapped[Optional[str]] = mapped_column(Text)
    locale: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    characters: Mapped[List['Characters']] = relationship('Characters', back_populates='account')


