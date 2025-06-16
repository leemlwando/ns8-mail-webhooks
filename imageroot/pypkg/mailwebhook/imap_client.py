import imaplib
import email
import os
from typing import List, Dict, Generator
from email.header import decode_header

class SimpleIMAPClient:
    def __init__(self):
        self.host = os.getenv('MAIL_SERVER', 'localhost')
        self.port = int(os.getenv('MAIL_PORT', '993'))
        self.connection = None
    
    def connect(self, username: str, password: str) -> bool:
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(username, password)
            return True
        except Exception as e:
            print(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    def list_mailboxes(self) -> List[str]:
        """List available mailboxes"""
        if not self.connection:
            return []
        
        try:
            status, mailboxes = self.connection.list()
            if status != 'OK':
                return []
            
            mailbox_names = []
            for mailbox in mailboxes:
                # Parse mailbox name from IMAP LIST response
                parts = mailbox.decode().split('"')
                if len(parts) >= 3:
                    mailbox_names.append(parts[-2])
            
            return mailbox_names
        except Exception as e:
            print(f"Error listing mailboxes: {e}")
            return []
    
    def get_messages(self, mailbox: str, unread_only: bool = True) -> Generator[Dict, None, None]:
        if not self.connection:
            return
        
        try:
            self.connection.select(mailbox)
            
            # Search for messages
            search_criteria = 'UNSEEN' if unread_only else 'ALL'
            status, messages = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                return
            
            message_ids = messages[0].split()
            
            for msg_id in message_ids:
                try:
                    # Fetch the message
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    yield {
                        'id': msg_id.decode(),
                        'subject': self._decode_header(email_message.get('Subject', '')),
                        'from': email_message.get('From', ''),
                        'to': email_message.get('To', ''),
                        'date': email_message.get('Date', ''),
                        'body': self._get_body(email_message),
                        'raw': msg_data[0][1].decode('utf-8', errors='ignore')
                    }
                    
                except Exception as e:
                    print(f"Error processing message {msg_id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error accessing mailbox {mailbox}: {e}")
    
    def mark_as_read(self, message_id: str):
        if self.connection:
            try:
                self.connection.store(message_id, '+FLAGS', '\\Seen')
            except Exception as e:
                print(f"Error marking message as read: {e}")
    
    def delete_message(self, message_id: str):
        if self.connection:
            try:
                self.connection.store(message_id, '+FLAGS', '\\Deleted')
                self.connection.expunge()
            except Exception as e:
                print(f"Error deleting message: {e}")
    
    def _decode_header(self, header: str) -> str:
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_header = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_header += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_header += part
                
        return decoded_header
    
    def _get_body(self, email_message) -> str:
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode('utf-8', errors='ignore')
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                return payload.decode('utf-8', errors='ignore')
        return ""
