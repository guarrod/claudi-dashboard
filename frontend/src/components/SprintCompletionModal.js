import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const SprintCompletionModal = ({
  visible,
  onClose,
  onSubmit,
  sprint,
  account,
  remainingBalance,
}) => {
  const [saveAmount, setSaveAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [saveSuggestion, setSaveSuggestion] = useState(null);

  useEffect(() => {
    if (visible && remainingBalance) {
      setSaveAmount(remainingBalance.toFixed(2));
      setSaveSuggestion(remainingBalance);
    }
  }, [visible, remainingBalance]);

  const handleSubmit = async () => {
    if (!saveAmount) {
      alert('Por favor ingresa un monto');
      return;
    }

    const amount = parseFloat(saveAmount);
    if (amount < 0) {
      alert('El monto debe ser positivo');
      return;
    }

    if (amount > remainingBalance) {
      alert('El monto no puede exceder el saldo disponible');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        save_amount: amount > 0 ? amount : 0,
      });
      setSaveAmount('');
      onClose();
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      onRequestClose={onClose}
      transparent={true}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <Text style={styles.title}>Completar Sprint</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close" size={24} color="#000" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content}>
            {/* Sprint Info */}
            <View style={styles.infoCard}>
              <Text style={styles.label}>Sprint</Text>
              <Text style={styles.value}>
                Sprint {sprint?.sprint_number || '?'}
              </Text>
              <Text style={styles.date}>
                {sprint?.start_date} - {sprint?.end_date}
              </Text>
            </View>

            {/* Account Info */}
            <View style={styles.infoCard}>
              <Text style={styles.label}>Cuenta</Text>
              <Text style={styles.value}>{account?.name || 'N/A'}</Text>
            </View>

            {/* Remaining Balance */}
            <View style={[styles.infoCard, styles.balanceCard]}>
              <Text style={styles.label}>Saldo Disponible</Text>
              <Text style={styles.balanceAmount}>
                ${remainingBalance?.toFixed(2) || '0.00'}
              </Text>
              <Text style={styles.balanceNote}>
                Este es el dinero que quedó después de completar los compromisos del sprint
              </Text>
            </View>

            {/* Savings Suggestion */}
            {saveSuggestion > 0 && (
              <View style={styles.suggestionCard}>
                <View style={styles.suggestionIcon}>
                  <Ionicons name="bulb" size={20} color="#007AFF" />
                </View>
                <View style={styles.suggestionText}>
                  <Text style={styles.suggestionTitle}>Sugerencia de Ahorros</Text>
                  <Text style={styles.suggestionSubtext}>
                    Te sugerimos guardar ${saveSuggestion.toFixed(2)} en tu cuenta de ahorros
                  </Text>
                </View>
              </View>
            )}

            {/* Amount Input */}
            <View style={styles.formGroup}>
              <Text style={styles.label}>Monto a Ahorrar</Text>
              <View style={styles.amountContainer}>
                <Text style={styles.currency}>$</Text>
                <TextInput
                  style={styles.amountInput}
                  placeholder="0.00"
                  value={saveAmount}
                  onChangeText={setSaveAmount}
                  keyboardType="decimal-pad"
                  editable={!loading}
                />
              </View>
              <Text style={styles.note}>
                Dejar en blanco o colocar 0 para completar sin ahorrar
              </Text>
            </View>
          </ScrollView>

          {/* Buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
              disabled={loading}
            >
              <Text style={styles.cancelButtonText}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.button,
                styles.submitButton,
                loading && styles.submitButtonDisabled,
              ]}
              onPress={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>Completar Sprint</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingTop: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  infoCard: {
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: '#999',
    marginBottom: 4,
  },
  value: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  date: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  balanceCard: {
    backgroundColor: '#f0fff4',
    borderWidth: 1,
    borderColor: '#34C759',
  },
  balanceAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#34C759',
    marginTop: 8,
  },
  balanceNote: {
    fontSize: 11,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  suggestionCard: {
    backgroundColor: '#f0f7ff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  suggestionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  suggestionText: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#007AFF',
  },
  suggestionSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  formGroup: {
    marginBottom: 40,
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginTop: 8,
  },
  currency: {
    fontSize: 18,
    fontWeight: '600',
    color: '#34C759',
    marginRight: 8,
  },
  amountInput: {
    flex: 1,
    paddingHorizontal: 8,
    paddingVertical: 12,
    fontSize: 16,
    color: '#000',
  },
  note: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
  buttonContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 24,
    gap: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
  },
  cancelButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#34C759',
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SprintCompletionModal;
