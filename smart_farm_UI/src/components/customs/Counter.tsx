import { useAppDispatch, useAppSelector } from '@/stores/hook.store'
import {
    increment,
    decrement,
    incrementByAmount,
} from '@/stores/counter.store'

export default function Counter() {
    const count = useAppSelector((state) => state.counter.value)
    const dispatch = useAppDispatch()

    return (
        <div>
            <h2>Count: {count}</h2>
            <button onClick={() => dispatch(increment())}>+</button>
            <button onClick={() => dispatch(decrement())}>-</button>
            <button onClick={() => dispatch(incrementByAmount(5))}>+5</button>
        </div>
    )
}