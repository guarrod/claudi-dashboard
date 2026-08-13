import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Picker,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const CreateTransactionModal = ({ visible, onClose, onSubmit, accounts, categories }) => {
  const [concept, setConcept] = useState('');
  const [amount, setAmount] = useState('');
  const [accountId, setAccountId] = useState(accounts?.[0]?.id?.toString() || '');
  const [categoryId, setCategoryId] = useState(categories?.[0]?.id?.toString() || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!concept || !amount || !accountId) {
      alert('Por favor completa todos los campos');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        concept,
        amount: parseFloat(amount),
        account_id: parseInt(accountId),
        category_id: categoryId ? parseInt(categoryId) : null,
      });
      // Reset form
      setConcept('');
      setAmount('');
      setAccountId(accounts?.[0]?.id?.toString() || '');
      setCategoryId(categories?.[0]?.id?.toString() || '');
      onClose();
    } catch (error) {
      alert('Error al crear transacción: ' + error.message);
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
            <Text style={styles.title}>Nuevo Gasto</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close" size={24} color="#000" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.form}>
            {/* Concept */}
            <View style={styles.formGroup}>
              <Text style={styles.label}>Concepto *</Text>
              <TextInput
                style={styles.input}
                placeholder="ej: Netflix, Almuerzo, etc."
                value={concept}
                onChangeText={setConcept}
                editable={!loading}
              />
            </View>

            {/* Amount */}
            <View style={styles.formGroup}>
              <Text style={styles.label}>Monto *</Text>
              <View style={styles.amountContainer}>
                <Text style={styles.currency}>$</Text>
                <TextInput
                  style={styles.amountInput}
                  placeholder="0.00"
                  value={amount}
                  onChangeText={setAmount}
                  keyboardType="decimal-pad"
                  editable={!loading}
                />
              </View>
            </View>

            {/* Account */}
            <View style={styles.formGroup}>
              <Text style={styles.label}>Cuenta *</Text>
              <View style={styles.picker}>
                <Picker
                  selectedValue={accountId}
                  onValueChange={setAccountId}
                  enabled={!loading}
                >
                  {accounts?.map((acc) => (
                    <Picker.Item
                      key={acc.id}
                      label={acc.name}
                      value={acc.id.toString()}
                    />
                  ))}
                </Picker>
              </View>
            </View>

            {/* Category */}
            {categories && categories.length > 0 && (
              <View style={styles.formGroup}>
                <Text style={styles.label}>Categoría</Text>
                <View style={styles.picker}>
                  <Picker
                    selectedValue={categoryId}
                    onValueChange={setCategoryId}
                    enabled={!loading}
                  >
                    <Picker.Item label="Sin categoría" value="" />
                    {categories.map((cat) => (
                      <Picker.Item
                        key={cat.id}
                        label={cat.name}
                        value={cat.id.toString()}
                      />
                    ))}
                  </Picker>
                </View>
              </View>
            )}

            <Text style={styles.note}>* Campos requeridos</Text>
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
              style={[styles.button, styles.submitButton, loading && styles.submitButtonDisabled]}
              onPress={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>Crear</Text>
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
  form: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  formGroup: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#000',
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  currency: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    marginRight: 8,
  },
  amountInput: {
    flex: 1,
    paddingHorizontal: 8,
    paddingVertical: 12,
    fontSize: 16,
    color: '#000',
  },
  picker: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    overflow: 'hidden',
  },
  note: {
    fontSize: 12,
    color: '#999',
    marginBottom: 40,
    marginTop: -16,
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
    backgroundColor: '#007AFF',
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

export default CreateTransactionModal;
