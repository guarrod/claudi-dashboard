import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  PanResponder,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const TransactionItem = ({
  transaction,
  completionMethod = 'CHECKBOX',
  onToggle,
  onDelete,
}) => {
  const slideAnimation = useRef(new Animated.Value(0)).current;
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderMove: (evt, { dx }) => {
        if (completionMethod === 'SLIDE' || completionMethod === 'BOTH') {
          slideAnimation.setValue(dx);
        }
      },
      onPanResponderRelease: (evt, { dx }) => {
        const threshold = -100;
        if (dx < threshold) {
          // Swipe left
          Animated.timing(slideAnimation, {
            toValue: -120,
            duration: 300,
            useNativeDriver: false,
          }).start();
        } else if (dx > -threshold / 2) {
          // Snap back
          Animated.timing(slideAnimation, {
            toValue: 0,
            duration: 300,
            useNativeDriver: false,
          }).start();
        }
      },
    })
  ).current;

  const isCompleted = transaction.status === 'COMPLETED';
  const screenWidth = Dimensions.get('window').width;

  const handleCheckboxToggle = () => {
    onToggle(transaction.id, !isCompleted);
  };

  const handleDelete = () => {
    onDelete(transaction.id);
  };

  const slideAnimatedStyle = {
    transform: [{ translateX: slideAnimation }],
  };

  return (
    <View style={styles.container}>
      {/* Delete Action Button (visible on slide) */}
      <View style={styles.deleteAction}>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={handleDelete}
        >
          <Ionicons name="trash" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Main Card */}
      <Animated.View
        style={[styles.card, isCompleted && styles.cardCompleted, slideAnimatedStyle]}
        {...(completionMethod === 'SLIDE' || completionMethod === 'BOTH'
          ? panResponder.panHandlers
          : {})}
      >
        <View style={styles.leftContent}>
          {/* Checkbox (if enabled) */}
          {(completionMethod === 'CHECKBOX' || completionMethod === 'BOTH') && (
            <TouchableOpacity
              style={styles.checkbox}
              onPress={handleCheckboxToggle}
            >
              {isCompleted && (
                <Ionicons name="checkmark" size={20} color="#fff" />
              )}
            </TouchableOpacity>
          )}

          {/* Transaction Info */}
          <View style={styles.info}>
            <Text
              style={[
                styles.concept,
                isCompleted && styles.conceptCompleted,
              ]}
              numberOfLines={1}
            >
              {transaction.concept}
            </Text>
            <Text style={styles.status}>
              {transaction.transaction_type === 'EXPENSE' ? 'Gasto' : 'Otro'}
              {transaction.completion_method && ` • ${transaction.completion_method}`}
            </Text>
          </View>
        </View>

        {/* Amount */}
        <Text
          style={[
            styles.amount,
            isCompleted && styles.amountCompleted,
          ]}
        >
          ${transaction.amount.toFixed(2)}
        </Text>
      </Animated.View>

      {/* Slide hint */}
      {!isCompleted && (
        completionMethod === 'SLIDE' || completionMethod === 'BOTH'
      ) && (
        <Text style={styles.slideHint}>← Desliza para eliminar</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
    overflow: 'hidden',
    borderRadius: 12,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  cardCompleted: {
    backgroundColor: '#f0f0f0',
  },
  deleteAction: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: 120,
    backgroundColor: '#ff3b30',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
  },
  deleteButton: {
    padding: 16,
  },
  leftContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 32,
    height: 32,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#007AFF',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  info: {
    flex: 1,
  },
  concept: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  conceptCompleted: {
    color: '#999',
    textDecorationLine: 'line-through',
  },
  status: {
    fontSize: 12,
    color: '#666',
  },
  amount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 12,
  },
  amountCompleted: {
    color: '#999',
  },
  slideHint: {
    fontSize: 11,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 4,
    paddingLeft: 44,
  },
});

export default TransactionItem;
