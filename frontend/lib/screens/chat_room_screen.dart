import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ChatRoomScreen extends StatefulWidget {
  final String targetId;
  final bool isGroup;

  const ChatRoomScreen({
    super.key,
    required this.targetId,
    required this.isGroup,
  });

  @override
  State<ChatRoomScreen> createState() => _ChatRoomScreenState();
}

class _ChatRoomScreenState extends State<ChatRoomScreen> {
  final _messageController = TextEditingController();
  List<dynamic> _messages = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMessages();
    _connectWebSocket();
  }

  @override
  void dispose() {
    apiService.onMessageReceived = null;
    super.dispose();
  }

  Future<void> _loadMessages() async {
    final messages = await apiService.getMessages(
      groupId: widget.isGroup ? widget.targetId : null,
      otherUserId: widget.isGroup ? null : widget.targetId,
    );
    setState(() {
      _messages = messages;
      _isLoading = false;
    });
  }

  void _connectWebSocket() {
    apiService.connectWebSocket();
    apiService.onMessageReceived = (messageData) {
      // Filter incoming message if it belongs to this room
      bool isRelevant = false;
      if (widget.isGroup && messageData['group_id'] == widget.targetId) {
        isRelevant = true;
      } else if (!widget.isGroup && 
                (messageData['sender_id'] == widget.targetId || 
                 messageData['receiver_id'] == widget.targetId)) {
        isRelevant = true;
      }

      if (isRelevant) {
        setState(() {
          // Add to beginning since we usually display newest at bottom and list is reversed
          _messages.insert(0, messageData);
        });
      }
    };
  }

  Future<void> _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;
    
    final text = _messageController.text;
    _messageController.clear();

    // Optimistically add to UI
    final tempMsg = {
      'content': text,
      'sender_id': 'me', // Just for UI logic
      'created_at': DateTime.now().toIso8601String(),
    };
    setState(() {
      _messages.insert(0, tempMsg);
    });

    final success = await apiService.sendMessage(
      text,
      groupId: widget.isGroup ? widget.targetId : null,
      receiverId: widget.isGroup ? null : widget.targetId,
    );

    if (!success) {
      // Handle failure (e.g., remove optimistic message, show error)
      debugPrint("Failed to send message");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.isGroup ? 'Group Chat' : 'Chat'),
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : ListView.builder(
                  reverse: true,
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final isMe = msg['sender_id'] == 'me'; 
                    // In a real app, compare with your own UUID
                    return Align(
                      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isMe ? Colors.blue[100] : Colors.grey[200],
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(msg['content'] ?? ''),
                      ),
                    );
                  },
                ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}
