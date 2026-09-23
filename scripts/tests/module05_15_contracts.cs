using VarianceDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
ISource<Cat> cats=new SingleValueSource<Cat>(new Cat("A"));ISource<Animal> animals=cats;Check(ReferenceEquals(cats,animals)&&ReferenceEquals(cats.Next(),animals.Next()),"variance cloned");Animal[] array=new Cat[1];Throws<ArrayTypeMismatchException>(()=>array[0]=new Dog("B"));
}
}
