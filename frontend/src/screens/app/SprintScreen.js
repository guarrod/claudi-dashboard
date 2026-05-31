import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../../config/api';
import TransactionItem from '../../components/TransactionItem';
import CreateTransactionModal from '../../components/CreateTransactionModal';
import { setTransactions, updateTransaction } from '../../redux/slices/transactionSlice';

const SprintScreen = () => {
  const { user } = useSelector((state) => state.auth);
  const { activeSprint } = useSelector((state) => state.sprint);
  const { completionMethod } = useSelector((state) => state.ui);
  const dispatch = useDispatch();
  const transactions = useSelector((state) => state.transaction.transactions);

  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (activeSprint?.id && user?.id) {
      fetchData();
    }
  }, [activeSprint, user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [transRes, accRes, catRes] = await Promise.all([
        apiClient.get(`/transactions/${activeSprint.id}?user_id=${user.id}`),
        apiClient.get(`/accounts/${user.id}`),
        apiClient.get(`/categories/${user.id}`),
      ]);
      dispatch(setTransactions(transRes.data));
      setAccounts(accRes.data);
      setCategories(catRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTransaction = async (data) => {
    try {
      setSubmitting(true);
      const response = await apiClient.post(
        `/transactions?user_id=${user.id}`,
        {
          sprint_id: activeSprint.id,
          ...data,
        }
      );
      dispatch(updateTransaction(response.data));
      // Refresh to recalculate available balance
      await fetchData();
    } catch (error) {
      console.error('Error creating transaction:', error);
      throw error;
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleTransaction = async (transactionId, isCompleting) => {
    try {
      const endpoint = isCompleting ? 'complete' : 'uncomplete';
      const response = await apiClient.patch(
        `/transactions/${transactionId}/${endpoint}?user_id=${user.id}`
      );
      dispatch(updateTransaction(response.data));
      // Refresh to recalculate available balance
      await fetchData();
    } catch (error) {
      console.error('Error toggling transaction:', error);
    }
  };

  const handleDeleteTransaction = async (transactionId) => {
    try {
      await apiClient.delete(
        `/transactions/${transactionId}?user_id=${user.id}`
      );
      fetchData();
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  const completedTotal = transactions
    .filter((t) => t.status === 'COMPLETED')
    .reduce((sum, t) => sum + t.amount, 0);

  const pendingTotal = transactions
    .filter((t) => t.status === 'PLANNED')
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Transacciones</Text>
          <Text style={styles.subtitle}>
            Sprint {activeSprint?.sprint_number || '?'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setModalVisible(true)}
        >
          <Ionicons name="add" size={28} color="#fff" />
        </TouchableOpacity>
      </View>

      <FlatList
        data={transactions}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TransactionItem
            transaction={item}
            completionMethod={completionMethod}
            onToggle={handleToggleTransaction}
            onDelete={handleDeleteTransaction}
          />
        )}
        ListHeaderComponent={
          <>
            {/* Summary Cards */}
            <View style={styles.summaryContainer}>
              <View style={[styles.summaryCard, styles.pendingCard]}>
                <Text style={styles.summaryLabel}>Por Completar</Text>
                <Text style={styles.summaryAmount}>
                  ${pendingTotal.toFixed(2)}
                </Text>
              </View>
              <View style={[styles.summaryCard, styles.completedCard]}>
                <Text style={styles.summaryLabel}>Completado</Text>
                <Text style={styles.summaryAmount}>
                  ${completedTotal.toFixed(2)}
                </Text>
              </View>
            </View>

            {transactions.length === 0 && (
              <View style={styles.emptyCard}>
                <Ionicons
                  name="document-outline"
                  size={48}
                  color="#ddd"
                  style={{ marginBottom: 12 }}
                />
                <Text style={styles.emptyText}>
                  No hay transacciones
                </Text>
                <Text style={styles.emptySubtext}>
                  Crea una nueva para comenzar
                </Text>
              </View>
            )}
          </>
        }
        ListEmptyComponent={null}
        contentContainerStyle={styles.listContent}
        scrollEnabled={false}
      />

      <CreateTransactionModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onSubmit={handleCreateTransaction}
        accounts={accounts}
        categories={categories}
      />
    </View>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    color: '#999',
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
  },
  summaryContainer: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
  },
  pendingCard: {
    backgroundColor: '#fff3cd',
  },
  completedCard: {
    backgroundColor: '#d4edda',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
  },
  summaryAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
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

export default SprintScreen;
