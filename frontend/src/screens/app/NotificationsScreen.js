import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  Alert,
} from 'react-native';
import { useSelector } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../../config/api';

const NotificationsScreen = () => {
  const { user } = useSelector((state) => state.auth);

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchNotifications();
    }
  }, [user]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/gmail/notifications/${user.id}?status=PENDING`
      );
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      Alert.alert('Error', 'No se pudieron cargar las notificaciones');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchNotifications();
    setRefreshing(false);
  };

  const handleConfirm = async (notificationId) => {
    setProcessingId(notificationId);
    try {
      await apiClient.post(
        `/gmail/notifications/${notificationId}/confirm`
      );
      setNotifications(
        notifications.filter((n) => n.id !== notificationId)
      );
      Alert.alert(
        'Éxito',
        'Gasto confirmado y marcado como completado'
      );
    } catch (error) {
      console.error('Error confirming notification:', error);
      Alert.alert('Error', 'No se pudo confirmar el gasto');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDiscard = async (notificationId) => {
    setProcessingId(notificationId);
    try {
      await apiClient.post(
        `/gmail/notifications/${notificationId}/discard`
      );
      setNotifications(
        notifications.filter((n) => n.id !== notificationId)
      );
    } catch (error) {
      console.error('Error discarding notification:', error);
      Alert.alert('Error', 'No se pudo descartar la notificación');
    } finally {
      setProcessingId(null);
    }
  };

  const syncGmail = async () => {
    setSyncing(true);
    try {
      await apiClient.post(`/gmail/sync?user_id=${user.id}`);
      await fetchNotifications();
      Alert.alert('Éxito', 'Emails sincronizados correctamente');
    } catch (error) {
      console.error('Error syncing Gmail:', error);
      Alert.alert('Error', 'No se pudieron sincronizar los emails');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Notificaciones</Text>
          <Text style={styles.subtitle}>
            Gastos detectados en tus emails
          </Text>
        </View>
        <TouchableOpacity
          onPress={syncGmail}
          disabled={syncing}
          style={styles.syncButton}
        >
          {syncing ? (
            <ActivityIndicator color="#007AFF" size="small" />
          ) : (
            <Ionicons name="refresh" size={24} color="#007AFF" />
          )}
        </TouchableOpacity>
      </View>

      {notifications.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons
            name="checkmark-circle"
            size={48}
            color="#34C759"
            style={{ marginBottom: 12 }}
          />
          <Text style={styles.emptyText}>Todo al día</Text>
          <Text style={styles.emptySubtext}>
            No hay gastos pendientes de validación
          </Text>
        </View>
      ) : (
        <View style={styles.listContainer}>
          {notifications.map((notification) => (
            <View key={notification.id} style={styles.notificationCard}>
              <View style={styles.cardHeader}>
                <View style={styles.iconContainer}>
                  <Ionicons
                    name={getIconName(notification.type)}
                    size={24}
                    color="#007AFF"
                  />
                </View>
                <View style={styles.contentContainer}>
                  <Text style={styles.notificationTitle}>
                    {notification.content.concept ||
                      'Gasto Detectado'}
                  </Text>
                  <Text style={styles.notificationDate}>
                    {new Date(
                      notification.created_at
                    ).toLocaleDateString()}
                  </Text>
                </View>
              </View>

              {notification.content.amount && (
                <Text style={styles.amount}>
                  ${notification.content.amount.toFixed(2)}
                </Text>
              )}

              {notification.content.source && (
                <Text style={styles.source}>
                  Detectado en:{' '}
                  {notification.content.source}
                </Text>
              )}

              <View style={styles.actionButtons}>
                <TouchableOpacity
                  style={[
                    styles.button,
                    styles.discardButton,
                    processingId === notification.id &&
                      styles.buttonDisabled,
                  ]}
                  onPress={() => handleDiscard(notification.id)}
                  disabled={processingId === notification.id}
                >
                  <Text style={styles.discardButtonText}>
                    Descartar
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.button,
                    styles.confirmButton,
                    processingId === notification.id &&
                      styles.buttonDisabled,
                  ]}
                  onPress={() => handleConfirm(notification.id)}
                  disabled={processingId === notification.id}
                >
                  {processingId === notification.id ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.confirmButtonText}>
                      Confirmar
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const getIconName = (type) => {
  switch (type) {
    case 'EXPENSE_DETECTED':
      return 'card';
    case 'CARD_STATEMENT':
      return 'credit';
    default:
      return 'notification';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  syncButton: {
    padding: 8,
  },
  listContainer: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  notificationCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f0f7ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  contentContainer: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  notificationDate: {
    fontSize: 12,
    color: '#999',
  },
  amount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  source: {
    fontSize: 12,
    color: '#999',
    marginBottom: 12,
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  discardButton: {
    backgroundColor: '#f0f0f0',
  },
  discardButtonText: {
    color: '#333',
    fontSize: 14,
    fontWeight: '600',
  },
  confirmButton: {
    backgroundColor: '#007AFF',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 20,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#bbb',
  },
});

export default NotificationsScreen;
