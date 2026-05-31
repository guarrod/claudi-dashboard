import React from 'react';
import { View, Text, StyleSheet, ScrollView, Switch, TouchableOpacity } from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { setTheme, setCompletionMethod, setRequiresConfirmation } from '../../redux/slices/uiSlice';
import { logout } from '../../redux/slices/authSlice';

const SettingsScreen = () => {
  const dispatch = useDispatch();
  const { theme, completionMethod, requiresConfirmation } = useSelector((state) => state.ui);

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Configuración</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Tema</Text>
        <TouchableOpacity
          style={[styles.optionButton, theme === 'LIGHT' && styles.optionButtonActive]}
          onPress={() => dispatch(setTheme('LIGHT'))}
        >
          <Text style={styles.optionText}>Claro (Light)</Text>
          {theme === 'LIGHT' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.optionButton, theme === 'DARK' && styles.optionButtonActive]}
          onPress={() => dispatch(setTheme('DARK'))}
        >
          <Text style={styles.optionText}>Oscuro (Dark)</Text>
          {theme === 'DARK' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.optionButton, theme === 'SYSTEM' && styles.optionButtonActive]}
          onPress={() => dispatch(setTheme('SYSTEM'))}
        >
          <Text style={styles.optionText}>Sistema</Text>
          {theme === 'SYSTEM' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Método de Completación</Text>
        <TouchableOpacity
          style={[styles.optionButton, completionMethod === 'CHECKBOX' && styles.optionButtonActive]}
          onPress={() => dispatch(setCompletionMethod('CHECKBOX'))}
        >
          <Text style={styles.optionText}>Checkbox</Text>
          {completionMethod === 'CHECKBOX' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.optionButton, completionMethod === 'SLIDE' && styles.optionButtonActive]}
          onPress={() => dispatch(setCompletionMethod('SLIDE'))}
        >
          <Text style={styles.optionText}>Slide</Text>
          {completionMethod === 'SLIDE' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.optionButton, completionMethod === 'BOTH' && styles.optionButtonActive]}
          onPress={() => dispatch(setCompletionMethod('BOTH'))}
        >
          <Text style={styles.optionText}>Ambos</Text>
          {completionMethod === 'BOTH' && <Text style={styles.checkmark}>✓</Text>}
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Validación</Text>
        <View style={styles.switchOption}>
          <Text style={styles.optionText}>Requerir confirmación</Text>
          <Switch
            value={requiresConfirmation}
            onValueChange={(value) => dispatch(setRequiresConfirmation(value))}
            trackColor={{ false: '#767577', true: '#81c784' }}
            thumbColor={requiresConfirmation ? '#4caf50' : '#f4f3f4'}
          />
        </View>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutButtonText}>Cerrar sesión</Text>
      </TouchableOpacity>
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
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    color: '#333',
  },
  optionButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  optionButtonActive: {
    backgroundColor: '#f0f7ff',
  },
  optionText: {
    fontSize: 14,
    color: '#333',
  },
  checkmark: {
    fontSize: 18,
    color: '#007AFF',
    fontWeight: '600',
  },
  switchOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  logoutButton: {
    backgroundColor: '#ff3b30',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 40,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SettingsScreen;
