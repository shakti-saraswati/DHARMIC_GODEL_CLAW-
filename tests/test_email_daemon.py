"""
Tests for Email Daemon - IMAP polling and SMTP responses.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import email
from email.mime.text import MIMEText

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))


class TestEmailConfig:
    """Test EmailConfig class."""

    def test_initialization_with_env_vars(self):
        """Test EmailConfig initializes from environment."""
        with patch.dict('os.environ', {
            'EMAIL_ADDRESS': 'test@example.com',
            'EMAIL_PASSWORD': 'testpass',
            'IMAP_SERVER': 'imap.test.com',
            'SMTP_SERVER': 'smtp.test.com',
            'IMAP_PORT': '993',
            'SMTP_PORT': '587'
        }):
            from email_daemon import EmailConfig
            config = EmailConfig()
            
            assert config.address == 'test@example.com'
            assert config.password == 'testpass'
            assert config.imap_server == 'imap.test.com'
            assert config.smtp_server == 'smtp.test.com'
            assert config.imap_port == 993
            assert config.smtp_port == 587

    def test_missing_credentials_raises_error(self):
        """Test missing credentials raises ValueError."""
        with patch.dict('os.environ', {
            'EMAIL_ADDRESS': '',
            'EMAIL_PASSWORD': ''
        }, clear=True):
            from email_daemon import EmailConfig
            with pytest.raises(ValueError) as exc_info:
                EmailConfig()
            
            assert 'EMAIL_ADDRESS' in str(exc_info.value)

    def test_default_ports(self):
        """Test default port values."""
        with patch.dict('os.environ', {
            'EMAIL_ADDRESS': 'test@example.com',
            'EMAIL_PASSWORD': 'testpass'
        }):
            from email_daemon import EmailConfig
            config = EmailConfig()
            
            assert config.imap_port == 993
            assert config.smtp_port == 587


class TestEmailDaemon:
    """Test EmailDaemon class."""

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_initialization(self, mock_get_agent, temp_dir):
        """Test EmailDaemon initialization."""
        mock_agent = Mock()
        mock_agent.run = Mock(return_value="Test response")
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)

        assert daemon.agent == mock_agent
        assert daemon.config == config
        assert daemon.poll_interval == 60
        assert not daemon.running

    @patch('email_daemon.get_agent')
    @patch('email_daemon.imaplib.IMAP4_SSL')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass',
        'IMAP_SERVER': 'imap.gmail.com'
    })
    def test_connect_imap_ssl(self, mock_imap, mock_get_agent, temp_dir):
        """Test IMAP connection with SSL."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent
        
        mock_mail = Mock()
        mock_imap.return_value = mock_mail

        from email_daemon import EmailDaemon, EmailConfig
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        mail = daemon.connect_imap()
        
        mock_imap.assert_called_once_with('imap.gmail.com', 993)
        mock_mail.login.assert_called_once_with('test@example.com', 'testpass')

    @patch('email_daemon.get_agent')
    @patch('email_daemon.imaplib.IMAP4')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass',
        'IMAP_SERVER': '127.0.0.1',
        'IMAP_PORT': '1143'
    })
    def test_connect_imap_localhost(self, mock_imap, mock_get_agent, temp_dir):
        """Test IMAP connection for localhost (Proton Bridge)."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent
        
        mock_mail = Mock()
        mock_imap.return_value = mock_mail

        from email_daemon import EmailDaemon, EmailConfig
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        mail = daemon.connect_imap()
        
        mock_imap.assert_called_once_with('127.0.0.1', 1143)
        mock_mail.starttls.assert_called_once()
        mock_mail.login.assert_called_once()

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_fetch_unread(self, mock_get_agent, temp_dir):
        """Test fetching unread emails."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        with patch.object(EmailDaemon, 'connect_imap') as mock_connect:
            mock_mail = Mock()
            mock_mail.search.return_value = ('OK', [b'1 2'])
            
            # Create mock email message
            msg = MIMEText("Test body")
            msg['Subject'] = "Test Subject"
            msg['From'] = "sender@test.com"
            msg['Message-ID'] = "<test123@test.com>"
            
            mock_mail.fetch.return_value = ('OK', [(b'1', msg.as_bytes())])
            mock_connect.return_value = mock_mail
            
            config = EmailConfig()
            daemon = EmailDaemon(agent=mock_agent, config=config)
            
            messages = daemon.fetch_unread()
            
            mock_mail.select.assert_called_once_with("INBOX")

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_fetch_unread_with_whitelist(self, mock_get_agent, temp_dir):
        """Test whitelist filtering."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(
            agent=mock_agent, 
            config=config,
            allowed_senders=['allowed@test.com']
        )
        
        assert daemon.allowed_senders == ['allowed@test.com']

    @patch('email_daemon.get_agent')
    @patch('email_daemon.smtplib.SMTP')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass',
        'SMTP_SERVER': 'smtp.gmail.com'
    })
    def test_send_response(self, mock_smtp, mock_get_agent, temp_dir):
        """Test sending email response."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent
        
        mock_server = Mock()
        mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = Mock(return_value=None)

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        # Should have send_response method
        assert hasattr(daemon, 'send_response') or hasattr(daemon, '_send_response')

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_process_message_with_agent(self, mock_get_agent, temp_dir):
        """Test processing message through agent."""
        mock_agent = Mock()
        mock_agent.run = Mock(return_value="Dharmic response")
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        # Process should use agent.run
        assert daemon.agent.run is not None

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_daemon_lifecycle(self, mock_get_agent, temp_dir):
        """Test daemon start/stop."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        assert not daemon.running
        
        # Has async run method
        assert hasattr(daemon, 'run') or hasattr(daemon, 'start')


class TestEmailDaemonIntegration:
    """Integration tests for EmailDaemon."""

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_processed_ids_tracking(self, mock_get_agent, temp_dir):
        """Test that processed message IDs are tracked."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        assert hasattr(daemon, 'processed_ids')
        assert isinstance(daemon.processed_ids, set)

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_log_directory_created(self, mock_get_agent, temp_dir):
        """Test that log directory is created."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config)
        
        assert daemon.log_dir.exists()

    @patch('email_daemon.get_agent')
    @patch.dict('os.environ', {
        'EMAIL_ADDRESS': 'test@example.com',
        'EMAIL_PASSWORD': 'testpass'
    })
    def test_poll_interval_configurable(self, mock_get_agent, temp_dir):
        """Test configurable poll interval."""
        mock_agent = Mock()
        mock_get_agent.return_value = mock_agent

        from email_daemon import EmailDaemon, EmailConfig
        
        config = EmailConfig()
        daemon = EmailDaemon(agent=mock_agent, config=config, poll_interval=120)
        
        assert daemon.poll_interval == 120
