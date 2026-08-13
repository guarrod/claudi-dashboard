import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const TemplateItem = ({ template, onEdit, onDelete, onSelect, isSelected }) => {
  const handleDelete = () => {
    Alert.alert(
      'Eliminar Plantilla',
      `¿Estás seguro de que quieres eliminar "${template.name}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: () => onDelete(template.id),
        },
      ]
    );
  };

  const frequencyLabel = {
    MONTHLY: 'Mensual',
    BIWEEKLY: 'Quincenal',
    OTHER: 'Otra',
  };

  return (
    <View style={[styles.container, isSelected && styles.containerSelected]}>
      <TouchableOpacity
        style={styles.content}
        onPress={() => onSelect?.(template)}
      >
        {isSelected && (
          <View style={styles.checkbox}>
            <Ionicons name="checkmark" size={20} color="#fff" />
          </View>
        )}

        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={1}>
            {template.name}
          </Text>
          <Text style={styles.frequency}>
            {frequencyLabel[template.frequency] || 'Otro'}
          </Text>
        </View>

        <Text style={styles.amount}>${template.amount.toFixed(2)}</Text>
      </TouchableOpacity>

      {!isSelected && (
        <View style={styles.actions}>
          <TouchableOpacity onPress={() => onEdit(template)} style={styles.actionButton}>
            <Ionicons name="pencil" size={16} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={handleDelete}
            style={styles.actionButton}
          >
            <Ionicons name="trash" size={16} color="#ff3b30" />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 8,
    overflow: 'hidden',
    flexDirection: 'row',
    alignItems: 'center',
  },
  containerSelected: {
    backgroundColor: '#f0f7ff',
  },
  content: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  info: {
    flex: 1,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  frequency: {
    fontSize: 12,
    color: '#999',
  },
  amount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginHorizontal: 12,
  },
  actions: {
    flexDirection: 'row',
    paddingRight: 8,
  },
  actionButton: {
    padding: 8,
    marginHorizontal: 4,
  },
});

export default TemplateItem;
