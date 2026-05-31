import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import apiClient from '../../config/api';
import { setActiveSprint } from '../../redux/slices/sprintSlice';

const DashboardScreen = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { activeSprint } = useSelector((state) => state.sprint);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) {
      fetchActiveSprint();
    }
  }, [user]);

  const fetchActiveSprint = async () => {
    try {
      const response = await apiClient.get(`/sprints/${user.id}/active`);
      dispatch(setActiveSprint(response.data));
    } catch (error) {
      console.error('Error fetching sprint:', error);
    } finally {
      setLoading(false);
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
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>

      {activeSprint ? (
        <View style={styles.sprintCard}>
          <Text style={styles.sprintTitle}>Sprint Activo: {activeSprint.sprint_number}</Text>
          <Text style={styles.sprintDate}>
            {new Date(activeSprint.start_date).toLocaleDateString()} -{' '}
            {new Date(activeSprint.end_date).toLocaleDateString()}
          </Text>
        </View>
      ) : (
        <View style={styles.noSprintCard}>
          <Text style={styles.noSprintText}>No hay sprint activo</Text>
        </View>
      )}

      <View style={styles.accountsContainer}>
        <Text style={styles.sectionTitle}>Mis Cuentas</Text>
        <View style={styles.accountCard}>
          <Text style={styles.accountName}>Banco Principal</Text>
          <Text style={styles.accountBalance}>$0.00</Text>
        </View>
        <View style={styles.accountCard}>
          <Text style={styles.accountName}>Efectivo</Text>
          <Text style={styles.accountBalance}>$0.00</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  sprintCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  sprintTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  sprintDate: {
    fontSize: 14,
    color: '#666',
  },
  noSprintCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 24,
    marginBottom: 24,
    alignItems: 'center',
  },
  noSprintText: {
    fontSize: 16,
    color: '#999',
  },
  accountsContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  accountCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  accountName: {
    fontSize: 14,
    color: '#333',
  },
  accountBalance: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
  },
});

export default DashboardScreen;
