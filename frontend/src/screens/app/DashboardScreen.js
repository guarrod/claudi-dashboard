import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import apiClient from '../../config/api';
import { setActiveSprint } from '../../redux/slices/sprintSlice';

const DashboardScreen = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { activeSprint } = useSelector((state) => state.sprint);
  const [refreshing, setRefreshing] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    setLoadingData(true);
    try {
      try {
        const sprintRes = await apiClient.get(`/sprints/${user.id}/active`);
        dispatch(setActiveSprint(sprintRes.data));
      } catch (e) {
        console.log('Sprint error:', e.message);
      }

      try {
        const accRes = await apiClient.get(`/accounts/${user.id}`);
        setAccounts(accRes.data || []);
      } catch (e) {
        console.log('Accounts error:', e.message);
      }
    } finally {
      setLoadingData(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>Hola, {user?.email || 'Usuario'}</Text>
      </View>

      {loadingData && (
        <View style={styles.loadingBar}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.loadingText}>Cargando datos...</Text>
        </View>
      )}

      {activeSprint ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sprint {activeSprint.sprint_number}</Text>
          <Text style={styles.cardSubtitle}>
            {new Date(activeSprint.start_date).toLocaleDateString()} - {new Date(activeSprint.end_date).toLocaleDateString()}
          </Text>
          {activeSprint.total_budget && (
            <Text style={styles.cardAmount}>Presupuesto: ${activeSprint.total_budget.toFixed(2)}</Text>
          )}
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sin Sprint Activo</Text>
          <Text style={styles.cardSubtitle}>Crea uno nuevo en la sección Sprints</Text>
        </View>
      )}

      {accounts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Cuentas</Text>
          {accounts.map((acc) => (
            <View key={acc.id} style={styles.accountItem}>
              <View>
                <Text style={styles.accountName}>{acc.name}</Text>
                <Text style={styles.accountType}>{acc.account_type}</Text>
              </View>
              <Text style={styles.accountBalance}>
                ${(acc.available_balance || 0).toFixed(2)}
              </Text>
            </View>
          ))}
        </View>
      )}

      <View style={styles.footer}>
        <Text style={styles.footerText}>Usa las otras pestañas para gestionar tu presupuesto</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  loadingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    margin: 16,
    backgroundColor: '#f0f7ff',
    borderRadius: 8,
  },
  loadingText: {
    fontSize: 12,
    color: '#666',
  },
  card: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#007AFF',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  cardAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  accountItem: {
    backgroundColor: '#fff',
    padding: 12,
    marginBottom: 8,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  accountName: {
    fontSize: 14,
    fontWeight: '500',
  },
  accountType: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  accountBalance: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#34C759',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
});

export default DashboardScreen;
