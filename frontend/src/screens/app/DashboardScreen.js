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
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../../config/api';
import { setActiveSprint } from '../../redux/slices/sprintSlice';

const DashboardScreen = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { activeSprint } = useSelector((state) => state.sprint);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    if (user?.id) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);

      try {
        const sprintRes = await apiClient.get(`/sprints/${user.id}/active`);
        dispatch(setActiveSprint(sprintRes.data));
      } catch (sprintError) {
        console.error('Error fetching sprint:', sprintError);
        dispatch(setActiveSprint(null));
      }

      try {
        const accRes = await apiClient.get(`/accounts/${user.id}`);
        setAccounts(accRes.data || []);
      } catch (accError) {
        console.error('Error fetching accounts:', accError);
        setAccounts([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  const daysLeft = activeSprint
    ? Math.ceil(
        (new Date(activeSprint.end_date) - new Date()) / (1000 * 60 * 60 * 24)
      )
    : 0;

  const totalBalance = accounts.reduce((sum, acc) => sum + (acc.current_balance || 0), 0);
  const totalAvailable = accounts.reduce(
    (sum, acc) => sum + (acc.available_balance || 0),
    0
  );

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>Bienvenido, {user?.email}</Text>
      </View>

      {activeSprint ? (
        <View style={styles.sprintCard}>
          <View style={styles.sprintHeader}>
            <View>
              <Text style={styles.sprintTitle}>
                Sprint {activeSprint.sprint_number}
              </Text>
              <Text style={styles.sprintDate}>
                {new Date(activeSprint.start_date).toLocaleDateString()} -{' '}
                {new Date(activeSprint.end_date).toLocaleDateString()}
              </Text>
            </View>
            <View style={styles.daysLeftBadge}>
              <Text style={styles.daysLeftNumber}>{Math.max(0, daysLeft)}</Text>
              <Text style={styles.daysLeftLabel}>días</Text>
            </View>
          </View>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${Math.min(100, (30 - daysLeft) / 0.3)}%` },
              ]}
            />
          </View>
        </View>
      ) : (
        <View style={styles.noSprintCard}>
          <Ionicons name="calendar-outline" size={32} color="#ddd" />
          <Text style={styles.noSprintText}>No hay sprint activo</Text>
          <Text style={styles.noSprintSubtext}>Crea uno para comenzar</Text>
        </View>
      )}

      {/* Totales */}
      <View style={styles.totalsContainer}>
        <View style={styles.totalCard}>
          <View style={styles.totalIcon}>
            <Ionicons name="wallet-outline" size={24} color="#007AFF" />
          </View>
          <View>
            <Text style={styles.totalLabel}>Balance Total</Text>
            <Text style={styles.totalAmount}>${totalBalance.toFixed(2)}</Text>
          </View>
        </View>
        <View style={styles.totalCard}>
          <View style={styles.totalIcon}>
            <Ionicons name="checkmark-circle-outline" size={24} color="#34C759" />
          </View>
          <View>
            <Text style={styles.totalLabel}>Disponible</Text>
            <Text style={styles.totalAmount}>${totalAvailable.toFixed(2)}</Text>
          </View>
        </View>
      </View>

      {/* Cuentas */}
      <View style={styles.accountsSection}>
        <Text style={styles.sectionTitle}>Mis Cuentas</Text>
        {accounts.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No hay cuentas registradas</Text>
          </View>
        ) : (
          accounts.map((account) => (
            <View key={account.id} style={styles.accountCard}>
              <View style={styles.accountInfo}>
                <View style={styles.accountIconContainer}>
                  <Ionicons
                    name={
                      account.account_type === 'BANK'
                        ? 'business-outline'
                        : account.account_type === 'CASH'
                        ? 'cash-outline'
                        : 'card-outline'
                    }
                    size={20}
                    color="#007AFF"
                  />
                </View>
                <View>
                  <Text style={styles.accountName}>{account.name}</Text>
                  <Text style={styles.accountType}>
                    {account.account_type === 'BANK'
                      ? 'Banco'
                      : account.account_type === 'CASH'
                      ? 'Efectivo'
                      : 'Tarjeta'}
                  </Text>
                </View>
              </View>
              <View style={styles.accountBalance}>
                <Text style={styles.balanceSmall}>
                  ${(account.available_balance || 0).toFixed(2)}
                </Text>
                <Text style={styles.balanceLabel}>disponible</Text>
              </View>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
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
  sprintCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  sprintHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sprintTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  sprintDate: {
    fontSize: 12,
    color: '#666',
  },
  daysLeftBadge: {
    backgroundColor: '#f0f7ff',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  daysLeftNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  daysLeftLabel: {
    fontSize: 10,
    color: '#666',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#f0f0f0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
  },
  noSprintCard: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 16,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  noSprintText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
    marginTop: 12,
  },
  noSprintSubtext: {
    fontSize: 14,
    color: '#bbb',
    marginTop: 4,
  },
  totalsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 20,
    gap: 12,
  },
  totalCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  totalIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f7ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  totalAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  accountsSection: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  accountCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  accountInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  accountIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f7ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  accountName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  accountType: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  accountBalance: {
    alignItems: 'flex-end',
  },
  balanceSmall: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  balanceLabel: {
    fontSize: 10,
    color: '#999',
    marginTop: 2,
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
  },
});

export default DashboardScreen;
