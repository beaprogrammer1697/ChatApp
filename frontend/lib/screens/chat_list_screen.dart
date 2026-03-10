import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'chat_room_screen.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  // In a real app, you'd fetch user's recent chats and groups.
  // For demonstration, we'll just have standard static entry points 
  // or a way to enter a receiver ID or group ID.

  final _targetIdController = TextEditingController();
  bool _isGroup = false;

  void _openChat() {
    if (_targetIdController.text.isEmpty) return;
    
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ChatRoomScreen(
          targetId: _targetIdController.text,
          isGroup: _isGroup,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chats'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              apiService.disconnectWebSocket();
              Navigator.pushReplacementNamed(context, '/login');
            },
          )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Text('Enter a User ID or Group ID to start chatting:'),
            const SizedBox(height: 16),
            TextField(
              controller: _targetIdController,
              decoration: const InputDecoration(
                labelText: 'Target UUID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('Is Group ID?'),
                Switch(
                  value: _isGroup,
                  onChanged: (val) => setState(() => _isGroup = val),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _openChat,
              child: const Text('Open Chat Room'),
            ),
            const SizedBox(height: 32),
            const Text(
              'Note: In a full app, this page would fetch and display a list of your recent conversations and groups from the backend via an API like GET /users/me/chats',
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            )
          ],
        ),
      ),
    );
  }
}
