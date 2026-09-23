using RefactoringDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var service=new LabelService(new ShippingCostPolicy());var cases=new List<LabelCase>();
 foreach(var w in new[]{0m,.4m,1.999m,2m,2.001m,18m})foreach(var speed in new[]{DeliverySpeed.Standard,DeliverySpeed.Express})
  cases.Add(new LabelCase("Nguyễn An","S","C","0",0,"vnd",w,speed));
 var result=CharacterizationHarness.Compare(cases,service);Check(result.Failed==0 && result.Passed==12,"boundary characterization");
 Check(new ShippingCostPolicy().Calculate(new Parcel(2,DeliverySpeed.Express),"vnd").Amount==45000,"independent oracle");
 var before=LegacyLabelBuilder.BuildLabel("A","S","C","Z",1," vnd ",1,false);
 var after=service.Create("A",new Address("S","C","Z"),new Parcel(1,DeliverySpeed.Standard),Money.Of(1," vnd ")).Render();Check(before!=after,"documented currency trim change");
 Check(new Money(-1,"vnd").Amount==-1,"factory not global invariant");Throws<ArgumentOutOfRangeException>(()=>Money.Of(-1,"vnd"));

 }

}
